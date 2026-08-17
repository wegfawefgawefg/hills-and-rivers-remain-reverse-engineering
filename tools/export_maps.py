#!/usr/bin/env python3
"""Export every shipped map record to reviewable JSON without changing sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from content_catalog import MAP_PACK_NAMES, parse_map_pack, parse_map_record


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export_record(pack_name: str, index: int, offset: int, record: bytes) -> dict:
    parsed = parse_map_record(record)
    bases = []
    for base in parsed["bases"]:
        if base["type"] == -1:
            continue
        bases.append({key: value for key, value in base.items() if key != "raw"})

    return {
        "pack": pack_name,
        "record_index": index,
        "source_offset": offset,
        "source_size": len(record),
        "sha256": sha256(record),
        "format_marker": parsed["format_marker"],
        "width": parsed["map_width"],
        "height": parsed["map_height"],
        "field_0x599_signed": parsed["field_0x599_signed"],
        "field_0x59a": parsed["field_0x59a"],
        "bases": bases,
        "cell_planes": [
            {
                "index": plane["index"],
                "offset": plane["offset"],
                "size": len(plane["raw"]),
                "sha256": sha256(plane["raw"]),
                "hex": plane["raw"].hex(),
            }
            for plane in parsed["cell_planes"]
        ],
        "labels": [
            {key: value for key, value in label.items() if key != "raw"}
            for label in parsed["labels"]
        ],
        "text_slots": [
            {key: value for key, value in slot.items() if key != "raw"}
            for slot in parsed["text_slots"]
            if slot["raw"]
        ],
        "events": [
            {
                "index": event["index"],
                "offset": event["offset"],
                "header_hex": event["header"].hex(),
                "commands": [
                    {
                        "index": command["index"],
                        "offset": command["offset"],
                        "opcode": command["opcode"],
                        "payload_hex": command["payload"].hex(),
                    }
                    for command in event["commands"]
                ],
            }
            for event in parsed["events"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path, help="extracted .app directory")
    parser.add_argument("output", type=Path, help="JSON output path")
    args = parser.parse_args()

    packs = []
    for pack_name in MAP_PACK_NAMES:
        version, records = parse_map_pack(args.app / pack_name)
        packs.append(
            {
                "name": pack_name,
                "version": version,
                "records": [
                    export_record(pack_name, index, offset, record)
                    for index, (offset, record) in enumerate(records)
                ],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"packs": packs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {sum(len(pack['records']) for pack in packs)} maps to {args.output}")


if __name__ == "__main__":
    main()
