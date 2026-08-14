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


def map_record_metadata(record: bytes) -> dict[str, int | str]:
    if len(record) <= 0x59A:
        raise ValueError("map record is shorter than its fixed metadata prefix")
    marker = record[0]
    width = record[0x597]
    height = record[0x598]
    if marker != ord("1"):
        raise ValueError(f"unsupported map record marker 0x{marker:02x}")
    if width == 0 or height == 0:
        raise ValueError("map record has a zero dimension")
    dynamic_cursor = 0x59C + 4 * width * height
    if dynamic_cursor >= len(record):
        raise ValueError("map record dynamic cursor exceeds record boundary")
    return {
        "format_marker": chr(marker),
        "map_width": width,
        "map_height": height,
        "field_0x599_signed": int.from_bytes(record[0x599:0x59A], signed=True),
        "field_0x59a": record[0x59A],
        "post_cell_planes_cursor_candidate": dynamic_cursor,
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
