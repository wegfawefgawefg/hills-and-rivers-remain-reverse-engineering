#!/usr/bin/env python3
"""Decode authored HRR content into stable, provenance-backed catalogue rows."""

from __future__ import annotations

import hashlib
import json
import plistlib
import re
import sqlite3
import struct
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote


MAP_PACK_NAMES = ("map.dat", "freemap.dat", "trial_map.dat", "tgs2009_map.dat")
MAP_BASE_OFFSET = 0x1F
MAP_BASE_COUNT = 100
MAP_BASE_SIZE = 14
MAP_WIDTH_OFFSET = 0x597
MAP_HEIGHT_OFFSET = 0x598
MAP_CELL_DATA_OFFSET = 0x59B
MAP_TEXT_SLOT_COUNT = 256
BASE_TYPE_NAMES = {
    -1: "unused",
    0: "route",
    1: "castle",
    2: "stable",
    3: "port",
    4: "cannon",
    5: "fort",
    6: "gold-mine-active",
    7: "gold-mine-spent",
}
MAP_DIRECTIONS = ("up", "down", "left", "right")
ITEM_NAMES = (
    "Speed-up", "Battle", "Offense", "Defense", "Hold",
    "Shield", "Teleporter", "Bomb", "Field HQ", "Draft",
    "Speed-up A", "Battle A", "Offense A", "Defense A", "Hold A",
    "Shield A", "Teleporter A", "Bomb A", "Field HQ A", "Draft A",
    "Speed-up S", "Battle S", "Offense S", "Defense S", "Hold S",
    "Shield S", "Teleporter S", "Bomb S", "Field HQ S", "Draft S",
)
LOADER_SYMBOLS = {
    "map-pack": "MapData::readPackData(int) const",
    "yas-file": "yas::Animation::open(char const*)",
}
STRINGS_PAIR = re.compile(r'"((?:\\.|[^"\\])*)"\s*=\s*"((?:\\.|[^"\\])*)"\s*;')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_id(kind: str, *parts: str) -> str:
    encoded = (quote(part, safe="._-") for part in parts)
    return f"{kind}:" + "/".join(encoded)


def add_entry(
    connection: sqlite3.Connection,
    build_id: str,
    entry_id: str,
    kind: str,
    path: str,
    offset: int | None,
    data: bytes,
    label: str,
    confidence: str,
    states: tuple[int, int, int, int],
    metadata: dict[str, object] | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO content_entries (
            build_id, id, kind, source_path, source_offset, source_size,
            sha256, label, confidence, extracted, linked, understood,
            presented, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            build_id,
            entry_id,
            kind,
            path,
            offset,
            len(data),
            digest(data),
            label,
            confidence,
            *states,
            json.dumps(metadata or {}, sort_keys=True, ensure_ascii=False),
        ),
    )


def parse_map_pack(path: Path) -> tuple[int, list[tuple[int, bytes]]]:
    data = path.read_bytes()
    if len(data) < 8:
        raise ValueError(f"map pack is too short: {path}")
    version, count = struct.unpack_from(">HH", data)
    table_end = 4 + 4 * (count + 1)
    if table_end > len(data):
        raise ValueError(f"map pack offset table exceeds file: {path}")
    offsets = list(struct.unpack_from(f">{count + 1}I", data, 4))
    if version != 1:
        raise ValueError(f"unsupported map pack version {version}: {path}")
    if offsets[0] != table_end or offsets[-1] != len(data):
        raise ValueError(f"invalid map pack boundary: {path}")
    if any(left >= right for left, right in zip(offsets, offsets[1:])):
        raise ValueError(f"map pack offsets are not strictly increasing: {path}")
    return version, [
        (offsets[index], data[offsets[index] : offsets[index + 1]])
        for index in range(count)
    ]


def signed_byte(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def decode_map_text(data: bytes) -> str:
    return data.decode("shift_jis")


def parse_map_record(record: bytes) -> dict[str, object]:
    if len(record) <= 0x59A:
        raise ValueError("map record is shorter than its fixed metadata prefix")
    marker = record[0]
    width = record[MAP_WIDTH_OFFSET]
    height = record[MAP_HEIGHT_OFFSET]
    if marker != ord("1"):
        raise ValueError(f"unsupported map record marker 0x{marker:02x}")
    if width == 0 or height == 0:
        raise ValueError("map record has a zero dimension")
    bases = []
    for index in range(MAP_BASE_COUNT):
        offset = MAP_BASE_OFFSET + index * MAP_BASE_SIZE
        raw = record[offset : offset + MAP_BASE_SIZE]
        if len(raw) != MAP_BASE_SIZE:
            raise ValueError("map record ends inside its base table")
        packed_route = raw[7]
        base_type = signed_byte(raw[0])
        item_ids = [signed_byte(raw[i]) for i in (8, 10, 12)]
        bases.append(
            {
                "index": index,
                "offset": offset,
                "raw": raw,
                "type": base_type,
                "type_name": BASE_TYPE_NAMES.get(base_type, "unknown"),
                "owner": signed_byte(raw[1]),
                "initial_soldiers": raw[2],
                "neighbors": dict(
                    zip(MAP_DIRECTIONS, (signed_byte(value) for value in raw[3:7]))
                ),
                "route_requirements": dict(
                    zip(
                        MAP_DIRECTIONS,
                        ((packed_route >> shift) & 3 for shift in (6, 4, 2, 0)),
                    )
                ),
                "item_ids": item_ids,
                "item_names": [
                    ITEM_NAMES[item_id] if 0 <= item_id < len(ITEM_NAMES) else None
                    for item_id in item_ids
                ],
                "item_values": [raw[i] for i in (9, 11, 13)],
            }
        )

    cell_count = width * height
    planes = []
    cursor = MAP_CELL_DATA_OFFSET
    for index in range(2):
        end = cursor + cell_count * 2
        if end > len(record):
            raise ValueError("map record ends inside its skipped cell planes")
        planes.append({"index": index, "offset": cursor, "raw": record[cursor:end]})
        cursor = end

    if cursor >= len(record):
        raise ValueError("map record has no label table")
    label_count = record[cursor]
    label_table_offset = cursor
    cursor += 1
    labels = []
    for index in range(label_count):
        if cursor >= len(record):
            raise ValueError("map record ends before a label length")
        size = record[cursor]
        offset = cursor
        cursor += 1
        end = cursor + size
        if end > len(record):
            raise ValueError("map record ends inside a label")
        raw = record[cursor:end]
        labels.append(
            {"index": index, "offset": offset, "raw": raw, "text": decode_map_text(raw)}
        )
        cursor = end

    text_table_offset = cursor
    text_slots = []
    for index in range(MAP_TEXT_SLOT_COUNT):
        if cursor + 2 > len(record):
            raise ValueError("map record ends before a text-slot length")
        size = int.from_bytes(record[cursor : cursor + 2], "big")
        offset = cursor
        cursor += 2
        end = cursor + size
        if end > len(record):
            raise ValueError("map record ends inside a text slot")
        raw = record[cursor:end]
        text_slots.append(
            {"index": index, "offset": offset, "raw": raw, "text": decode_map_text(raw)}
        )
        cursor = end

    event_table_offset = cursor
    if cursor >= len(record):
        raise ValueError("map record has no event table")
    event_count = record[cursor]
    cursor += 1
    events = []
    for event_index in range(event_count):
        event_offset = cursor
        if cursor + 32 > len(record):
            raise ValueError("map record ends inside an event header")
        header = record[cursor : cursor + 30]
        command_count = int.from_bytes(record[cursor + 30 : cursor + 32], "big")
        cursor += 32
        commands = []
        for command_index in range(command_count):
            command_offset = cursor
            if cursor + 2 > len(record):
                raise ValueError("map record ends before a command header")
            opcode = record[cursor]
            payload_size = record[cursor + 1]
            cursor += 2
            end = cursor + payload_size
            if end > len(record):
                raise ValueError("map record ends inside a command payload")
            payload = record[cursor:end]
            commands.append(
                {
                    "index": command_index,
                    "offset": command_offset,
                    "opcode": opcode,
                    "payload": payload,
                    "raw": record[command_offset:end],
                }
            )
            cursor = end
        events.append(
            {
                "index": event_index,
                "offset": event_offset,
                "header": header,
                "commands": commands,
                "raw": record[event_offset:cursor],
            }
        )

    if cursor != len(record):
        raise ValueError(
            f"map record has {len(record) - cursor} unconsumed trailing bytes"
        )

    return {
        "format_marker": chr(marker),
        "map_width": width,
        "map_height": height,
        "field_0x599_signed": int.from_bytes(record[0x599:0x59A], signed=True),
        "field_0x59a": record[0x59A],
        "bases": bases,
        "cell_planes": planes,
        "label_table_offset": label_table_offset,
        "labels": labels,
        "text_table_offset": text_table_offset,
        "text_slots": text_slots,
        "event_table_offset": event_table_offset,
        "events": events,
        "end_offset": cursor,
    }


def map_record_metadata(record: bytes) -> dict[str, int | str]:
    parsed = parse_map_record(record)
    bases = parsed["bases"]
    text_slots = parsed["text_slots"]
    events = parsed["events"]
    return {
        "format_marker": parsed["format_marker"],
        "map_width": parsed["map_width"],
        "map_height": parsed["map_height"],
        "field_0x599_signed": parsed["field_0x599_signed"],
        "field_0x59a": parsed["field_0x59a"],
        "active_base_count": sum(base["type"] != -1 for base in bases),
        "label_count": len(parsed["labels"]),
        "nonempty_text_slot_count": sum(bool(slot["raw"]) for slot in text_slots),
        "event_count": len(events),
        "command_count": sum(len(event["commands"]) for event in events),
        "label_table_offset": parsed["label_table_offset"],
        "text_table_offset": parsed["text_table_offset"],
        "event_table_offset": parsed["event_table_offset"],
        "end_offset": parsed["end_offset"],
    }


def insert_map_packs(
    connection: sqlite3.Connection, build_id: str, app: Path
) -> None:
    hashes: dict[str, list[str]] = defaultdict(list)
    for name in MAP_PACK_NAMES:
        path = app / name
        relative = path.relative_to(app).as_posix()
        raw = path.read_bytes()
        version, records = parse_map_pack(path)
        pack_id = content_id("map-pack", relative)
        add_entry(
            connection,
            build_id,
            pack_id,
            "map-pack",
            relative,
            0,
            raw,
            f"Indexed map pack {name}",
            "confirmed",
            (1, 1, 0, 0),
            {"version": version, "record_count": len(records)},
        )
        for index, (offset, record) in enumerate(records):
            parsed = parse_map_record(record)
            record_metadata = map_record_metadata(record)
            record_metadata.update({"record_index": index, "pack_version": version})
            entry_id = content_id("map-record", relative, f"{index:03d}")
            add_entry(
                connection,
                build_id,
                entry_id,
                "map-record",
                relative,
                offset,
                record,
                f"{name} record {index}",
                "unknown",
                (1, 1, 0, 0),
                record_metadata,
            )
            connection.execute(
                "INSERT INTO map_pack_records VALUES (?, ?, ?, ?, ?)",
                (build_id, entry_id, relative, version, index),
            )
            connection.execute(
                "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                (build_id, pack_id, "contains", entry_id, "indexed offset table"),
            )

            for base in parsed["bases"]:
                if base["type"] == -1:
                    continue
                base_id = content_id(
                    "map-base", relative, f"{index:03d}", f"{base['index']:03d}"
                )
                add_entry(
                    connection,
                    build_id,
                    base_id,
                    "map-base",
                    relative,
                    offset + base["offset"],
                    base["raw"],
                    f"{name} record {index} base {base['index']}",
                    "confirmed",
                    (1, 1, 1, 0),
                    {
                        key: value
                        for key, value in base.items()
                        if key not in ("raw", "offset")
                    },
                )
                connection.execute(
                    "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                    (build_id, entry_id, "contains-base", base_id,
                     "MapData::LoadMapData 14-byte BASE_DATA source record"),
                )

            for plane in parsed["cell_planes"]:
                plane_id = content_id(
                    "map-cell-plane", relative, f"{index:03d}", str(plane["index"])
                )
                add_entry(
                    connection,
                    build_id,
                    plane_id,
                    "map-cell-plane",
                    relative,
                    offset + plane["offset"],
                    plane["raw"],
                    f"{name} record {index} skipped cell plane {plane['index']}",
                    "confirmed",
                    (1, 1, 0, 0),
                    {
                        "plane_index": plane["index"],
                        "cell_count": parsed["map_width"] * parsed["map_height"],
                        "bytes_per_cell": 2,
                        "loader_behavior": "cursor advance only",
                    },
                )
                connection.execute(
                    "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                    (build_id, entry_id, "contains-cell-plane", plane_id,
                     "fixed two bytes per map cell"),
                )

            for label in parsed["labels"]:
                label_id = content_id(
                    "map-label", relative, f"{index:03d}", f"{label['index']:03d}"
                )
                add_entry(
                    connection,
                    build_id,
                    label_id,
                    "map-label",
                    relative,
                    offset + label["offset"] + 1,
                    label["raw"],
                    f"{name} record {index} label {label['index']}",
                    "confirmed",
                    (1, 1, 1, 0),
                    {"slot": label["index"], "text": label["text"]},
                )
                connection.execute(
                    "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                    (build_id, entry_id, "contains-label", label_id,
                     "one-byte-length Shift-JIS table"),
                )

            for slot in parsed["text_slots"]:
                if not slot["raw"]:
                    continue
                text_id = content_id(
                    "map-text", relative, f"{index:03d}", f"{slot['index']:03d}"
                )
                add_entry(
                    connection,
                    build_id,
                    text_id,
                    "map-text",
                    relative,
                    offset + slot["offset"] + 2,
                    slot["raw"],
                    f"{name} record {index} text {slot['index']}",
                    "confirmed",
                    (1, 1, 1, 0),
                    {"slot": slot["index"], "text": slot["text"]},
                )
                connection.execute(
                    "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                    (build_id, entry_id, "contains-text", text_id,
                     "256-slot big-endian-length Shift-JIS table"),
                )

            for event in parsed["events"]:
                event_id = content_id(
                    "map-event", relative, f"{index:03d}", f"{event['index']:03d}"
                )
                add_entry(
                    connection,
                    build_id,
                    event_id,
                    "map-event",
                    relative,
                    offset + event["offset"],
                    event["raw"],
                    f"{name} record {index} event {event['index']}",
                    "confirmed",
                    (1, 1, 0, 0),
                    {
                        "event_index": event["index"],
                        "header_hex": event["header"].hex(),
                        "command_count": len(event["commands"]),
                    },
                )
                connection.execute(
                    "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                    (build_id, entry_id, "contains-event", event_id,
                     "Script::LoadMapEvent event table"),
                )
                for command in event["commands"]:
                    command_id = content_id(
                        "map-command", relative, f"{index:03d}",
                        f"{event['index']:03d}", f"{command['index']:03d}"
                    )
                    add_entry(
                        connection,
                        build_id,
                        command_id,
                        "map-command",
                        relative,
                        offset + command["offset"],
                        command["raw"],
                        (f"{name} record {index} event {event['index']} "
                         f"command {command['index']}"),
                        "confirmed",
                        (1, 1, 0, 0),
                        {
                            "opcode": command["opcode"],
                            "payload_hex": command["payload"].hex(),
                        },
                    )
                    connection.execute(
                        "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                        (build_id, event_id, "contains-command", command_id,
                         "opcode, one-byte payload size, payload"),
                    )
            hashes[digest(record)].append(entry_id)

    for identical_ids in hashes.values():
        canonical = identical_ids[0]
        for duplicate in identical_ids[1:]:
            connection.execute(
                "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                (build_id, duplicate, "byte-identical-to", canonical, "SHA-256 match"),
            )


def locale_and_table(path: Path, app: Path) -> tuple[str, str]:
    relative = path.relative_to(app)
    locale_parts = [part for part in relative.parts if part.endswith(".lproj")]
    if len(locale_parts) != 1:
        raise ValueError(f"cannot identify locale for strings file: {path}")
    locale = locale_parts[0].removesuffix(".lproj")
    return locale, path.stem


def decode_strings(raw: bytes, path: Path) -> tuple[dict[str, str], str]:
    try:
        values = plistlib.loads(raw)
        encoding = "Apple binary plist"
    except plistlib.InvalidFileException:
        text = raw.decode("utf-8-sig")
        values = {}
        for match in STRINGS_PAIR.finditer(text):
            key = json.loads(f'"{match.group(1)}"')
            value = json.loads(f'"{match.group(2)}"')
            values[key] = value
        if not values:
            raise ValueError(f"unrecognized strings syntax: {path}")
        encoding = "UTF-8 OpenStep strings"
    if not isinstance(values, dict):
        raise ValueError(f"strings file is not a dictionary: {path}")
    return values, encoding


def insert_strings(
    connection: sqlite3.Connection, build_id: str, app: Path
) -> None:
    logical_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path in sorted(app.rglob("*.strings")):
        raw = path.read_bytes()
        values, encoding = decode_strings(raw, path)
        relative = path.relative_to(app).as_posix()
        locale, table = locale_and_table(path, app)
        table_id = content_id("strings-table", locale, table)
        add_entry(
            connection,
            build_id,
            table_id,
            "strings-table",
            relative,
            0,
            raw,
            f"{locale} {table} strings",
            "confirmed",
            (1, 1, 1, 1),
            {"entry_count": len(values), "encoding": encoding},
        )
        for key, value in sorted(values.items(), key=lambda item: str(item[0])):
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"non-string localization entry in {path}")
            entry_id = content_id("string", locale, table, key)
            encoded = value.encode("utf-8")
            add_entry(
                connection,
                build_id,
                entry_id,
                "localized-string",
                relative,
                None,
                encoded,
                f"{table}[{key}] ({locale})",
                "confirmed",
                (1, 1, 1, 1),
                {"string_key": key, "table": table, "locale": locale},
            )
            connection.execute(
                "INSERT INTO localized_strings VALUES (?, ?, ?, ?, ?, ?)",
                (build_id, entry_id, locale, table, key, value),
            )
            connection.execute(
                "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                (build_id, table_id, "contains", entry_id, "decoded plist dictionary"),
            )
            logical_groups[(table, key)].append(entry_id)

    for variants in logical_groups.values():
        canonical = variants[0]
        for variant in variants[1:]:
            connection.execute(
                "INSERT INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                (build_id, variant, "localizes", canonical, "same table and key"),
            )


def c_string(data: bytes) -> str | None:
    value = data.split(b"\0", 1)[0]
    if not value:
        return None
    try:
        decoded = value.decode("ascii")
    except UnicodeDecodeError:
        return None
    return decoded if decoded.isprintable() else None


def insert_yas(connection: sqlite3.Connection, build_id: str, app: Path) -> None:
    resources = {
        path.relative_to(app).as_posix(): path for path in app.rglob("*") if path.is_file()
    }
    for path in sorted(app.rglob("*.yas")):
        raw = path.read_bytes()
        if len(raw) < 0x60 or raw[:4] != b"YAS\0":
            raise ValueError(f"invalid YAS header: {path}")
        words = list(struct.unpack_from("<8I", raw, 4))
        version = words[0]
        if version != 1:
            raise ValueError(f"unsupported YAS version {version}: {path}")
        relative = path.relative_to(app).as_posix()
        texture = c_string(raw[0x40:0x60])
        entry_id = content_id("yas", relative)
        add_entry(
            connection,
            build_id,
            entry_id,
            "yas-file",
            relative,
            0,
            raw,
            f"YAS animation {relative}",
            "probable",
            (1, 1, 0, 0),
            {"version": version, "header_words": words, "texture_name": texture},
        )
        connection.execute(
            "INSERT INTO yas_headers VALUES (?, ?, ?, ?, ?)",
            (build_id, entry_id, version, json.dumps(words), texture),
        )
        if texture:
            candidate = path.with_name(texture).relative_to(app).as_posix()
            if candidate in resources:
                texture_id = content_id("asset", candidate)
                texture_raw = resources[candidate].read_bytes()
                exists = connection.execute(
                    "SELECT 1 FROM content_entries WHERE build_id = ? AND id = ?",
                    (build_id, texture_id),
                ).fetchone()
                if not exists:
                    add_entry(
                        connection,
                        build_id,
                        texture_id,
                        "referenced-asset",
                        candidate,
                        0,
                        texture_raw,
                        f"Asset referenced by YAS animation",
                        "confirmed",
                        (1, 1, 0, 0),
                    )
                connection.execute(
                    "INSERT OR IGNORE INTO content_relationships VALUES (?, ?, ?, ?, ?)",
                    (build_id, entry_id, "references-texture", texture_id, "YAS header string"),
                )


def link_consumers(connection: sqlite3.Connection, build_id: str) -> None:
    for kind, symbol_name in LOADER_SYMBOLS.items():
        symbols = connection.execute(
            """
            SELECT architecture, virtual_address, COALESCE(demangled_name, name)
            FROM symbols
            WHERE build_id = ?
              AND (demangled_name = ? OR name = ?)
              AND virtual_address IS NOT NULL
            """,
            (build_id, symbol_name, symbol_name),
        ).fetchall()
        entries = connection.execute(
            "SELECT id FROM content_entries WHERE build_id = ? AND kind = ?",
            (build_id, kind),
        ).fetchall()
        for (entry_id,) in entries:
            for architecture, address, found_name in symbols:
                connection.execute(
                    "INSERT INTO consumer_callsites VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        build_id,
                        entry_id,
                        architecture,
                        address,
                        found_name,
                        "loads",
                        "surviving symbol and decompiled call path",
                    ),
                )


def insert_functional_content(
    connection: sqlite3.Connection, build_id: str, app: Path
) -> None:
    insert_map_packs(connection, build_id, app)
    insert_strings(connection, build_id, app)
    insert_yas(connection, build_id, app)
    link_consumers(connection, build_id)
