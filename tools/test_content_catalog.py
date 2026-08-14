#!/usr/bin/env python3
"""Focused tests for content-container boundary and strings decoding."""

from __future__ import annotations

import plistlib
import struct
import tempfile
import unittest
from pathlib import Path

from content_catalog import decode_strings, parse_map_pack


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


if __name__ == "__main__":
    unittest.main()
