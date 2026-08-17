#!/usr/bin/env python3
"""Focused tests for content-container boundary and strings decoding."""

from __future__ import annotations

import plistlib
import struct
import tempfile
import unittest
from pathlib import Path

from content_catalog import (
    decode_strings,
    map_record_metadata,
    parse_map_pack,
    parse_map_record,
)


class MapPackTests(unittest.TestCase):
    def write_pack(self, data: bytes, directory: str) -> Path:
        path = Path(directory) / "map.dat"
        path.write_bytes(data)
        return path

    def test_decodes_big_endian_offset_table(self) -> None:
        first = b"first"
        second = b"second record"
        header_size = 4 + 4 * 3
        raw = (
            struct.pack(">HHIII", 1, 2, header_size, header_size + len(first),
                        header_size + len(first) + len(second))
            + first
            + second
        )
        with tempfile.TemporaryDirectory() as directory:
            version, records = parse_map_pack(self.write_pack(raw, directory))
        self.assertEqual(version, 1)
        self.assertEqual(records, [(header_size, first), (header_size + 5, second)])

    def test_rejects_nonterminal_final_offset(self) -> None:
        raw = struct.pack(">HHII", 1, 1, 12, 13) + b"two"
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_pack(raw, directory)
            with self.assertRaisesRegex(ValueError, "invalid map pack boundary"):
                parse_map_pack(path)


class StringsTests(unittest.TestCase):
    def test_decodes_binary_plist(self) -> None:
        raw = plistlib.dumps({"Greeting": "Hello"}, fmt=plistlib.FMT_BINARY)
        values, encoding = decode_strings(raw, Path("Example.strings"))
        self.assertEqual(values, {"Greeting": "Hello"})
        self.assertEqual(encoding, "Apple binary plist")

    def test_decodes_utf8_openstep_strings(self) -> None:
        raw = '\ufeff/* comment */\n"Title" = "山河";\n'.encode()
        values, encoding = decode_strings(raw, Path("Root.strings"))
        self.assertEqual(values, {"Title": "山河"})
        self.assertEqual(encoding, "UTF-8 OpenStep strings")


class MapRecordTests(unittest.TestCase):
    def test_extracts_fixed_metadata_and_dynamic_cursor(self) -> None:
        event_offset = 0x59C + 4 * 15 * 21 + 256 * 2
        record = bytearray(event_offset + 1)
        record[0] = ord("1")
        record[0x597] = 15
        record[0x598] = 21
        record[0x599] = 0xF8
        metadata = map_record_metadata(bytes(record))
        self.assertEqual(metadata["map_width"], 15)
        self.assertEqual(metadata["map_height"], 21)
        self.assertEqual(metadata["field_0x599_signed"], -8)
        self.assertEqual(metadata["label_table_offset"], 0x59B + 4 * 15 * 21)
        self.assertEqual(metadata["event_table_offset"], event_offset)
        self.assertEqual(metadata["end_offset"], len(record))

    def test_decodes_base_text_and_event_sections(self) -> None:
        width = height = 1
        record = bytearray(0x59B + 4 * width * height)
        record[0] = ord("1")
        record[0x597] = width
        record[0x598] = height
        record[0x1F:0x2D] = bytes(
            [2, 1, 10, 0xFF, 2, 3, 4, 0b01101100, 5, 30, 6, 20, 7, 10]
        )
        label = "アラン".encode("shift_jis")
        text = "進め".encode("shift_jis")
        record += bytes([1, len(label)]) + label
        record += len(text).to_bytes(2, "big") + text
        record += bytes(2 * 255)
        event_header = bytes(range(30))
        command = bytes([7, 3, 0xAA, 0xBB, 0xCC])
        record += bytes([1]) + event_header + bytes([0, 1]) + command

        parsed = parse_map_record(bytes(record))
        base = parsed["bases"][0]
        self.assertEqual(base["type"], 2)
        self.assertEqual(base["owner"], 1)
        self.assertEqual(
            base["neighbors"], {"up": -1, "down": 2, "left": 3, "right": 4}
        )
        self.assertEqual(
            base["route_requirements"],
            {"up": 1, "down": 2, "left": 3, "right": 0},
        )
        self.assertEqual(parsed["labels"][0]["text"], "アラン")
        self.assertEqual(parsed["text_slots"][0]["text"], "進め")
        self.assertEqual(parsed["events"][0]["commands"][0]["opcode"], 7)
        self.assertEqual(
            parsed["events"][0]["commands"][0]["payload"], b"\xaa\xbb\xcc"
        )


if __name__ == "__main__":
    unittest.main()
