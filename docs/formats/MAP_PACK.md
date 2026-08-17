# Indexed map packs

`map.dat`, `freemap.dat`, `trial_map.dat`, and `tgs2009_map.dat` share a strict
big-endian indexed-container format:

```text
offset  size                 field
0x00    2                    version (currently 1)
0x02    2                    record_count
0x04    4 * (record_count+1) absolute record offsets
...     offsets[N+1]         concatenated record bytes
```

The first offset equals `4 + 4 * (record_count + 1)`, offsets are strictly
increasing, and the final offset equals the file size. A record `i` occupies
`[offset[i], offset[i+1])`. Integers in this outer header are big-endian.

| File | Records | Header bytes | File bytes | Record-size range |
| --- | ---: | ---: | ---: | ---: |
| `map.dat` | 13 | 60 | 105,397 | 3,259–15,044 |
| `freemap.dat` | 40 | 168 | 329,995 | 5,351–16,320 |
| `trial_map.dat` | 12 | 56 | 99,671 | 3,259–15,047 |
| `tgs2009_map.dat` | 13 | 60 | 106,114 | 3,259–15,047 |

Some generic `file` implementations misidentify the prefix as an Adobe swatch
file. The surviving game loader and the exact terminal offsets establish that
these are indexed game-data containers.

The ARMv6 pack consumer is `MapData::readPackData(int) const` at `0x6d6b8`; the
ARMv7 counterpart is at `0x6beec`. Both lead to
`FileManager::ReadBuffPackData(std::string const&, int, int)`.

## Complete structural record boundary

`tools/content_catalog.py::parse_map_record` now consumes every byte of all 78
records and rejects truncation or trailing data. The internal sections are:

```text
0x000                         format marker and regulation data
0x01f  100 * 14 bytes         route/base graph records
0x597                         dimensions and two map flags
0x59b  2 * width*height*2     two legacy cell planes
...    1 + Pascal strings     one-byte label count and Shift-JIS labels
...    256 * (u16 + bytes)    Shift-JIS text slots; big-endian lengths
...    1 + event records      event count and bytecode
EOF                           exact after final command payload
```

The fixed fields are:

| Record offset | Size | Interpretation | Confidence |
| ---: | ---: | --- | --- |
| `0x000` | 1 | ASCII format marker `1` | Confirmed by explicit rejection branch |
| `0x597` | 1 | map width in cells | Confirmed by multiplication and runtime-like values |
| `0x598` | 1 | map height in cells | Confirmed by multiplication and runtime-like values |
| `0x599` | 1 | signed field stored in `MapData + 0x20` | Meaning unknown |
| `0x59a` | 1 | boolean field stored in `MapData + 0x24` | Meaning unknown |

All 78 records pass these invariants. Width and height range from 15 to 30 and
include rectangular layouts such as 21×30, 24×18, and 27×30.

### Route/base graph

The 100 records correspond directly to the runtime `boost::array<BASE_DATA,
100>`. Their array index is also their matrix position: `x = index % 10`, `y =
index / 10`; the loader derives world coordinates as `x*160+240,
y*144+160`. Unused slots have type `-1`.

| Byte | Runtime field | Interpretation |
| ---: | --- | --- |
| 0 | `BASE_DATA + 0x00` | signed type: `-1` unused, `0` route, `1` castle, `2` stable, `3` port, `4` cannon, `5` fort, `6` active gold mine; runtime type `7` is an expired gold mine |
| 1 | `+0x04` | signed initial owner: `-1` neutral or faction `0..3` |
| 2 | `+0x08..+0x18` | initial soldier count, assigned to the owner/neutral bucket |
| 3..6 | `+0x34..+0x40` | neighbor indices in up, down, left, right order; `-1` means no edge |
| 7 | `+0x44..+0x50` | four packed two-bit route requirements, MSB pair first; shipped records use `0` open or `1` requires owning a port |
| 8,10,12 | `+0x64,+0x68,+0x6c` | three signed item IDs (`-1` empty, `0..29` the localized item table) |
| 9,11,13 | `+0x70,+0x74,+0x78` | unsigned drop threshold paired with each item ID; `ItemDrop` tests slots in order with independent `Random(0xff)` draws and awards the first success |

The special-base names are corroborated by the English `ExplainSpecialBase`
table and by behavior in `Scene::Game::SetBaseUser` at ARMv6 `0x2dda4`: type 2
recalculates troop speeds, type 4 maintains cannon targeting, and type 5 resets
its fort-construction timer. `turnEndFort` at `0x1c7f0` changes an occupied type
5 into a type-1 castle after five turn ends; `turnEndGoldMine` at `0x1c5a4`
changes an occupied type 6 into runtime type 7 after three. `IsPassable` at
`0x11b08` proves route requirement 1 checks
whether the moving faction owns at least one type-3 base (a port).

### Cell planes

Two planes begin at `0x59b`; each contains exactly `width*height` two-byte
cells. `MapData::LoadMapData` only advances over these bytes and never copies or
interprets them in this build, so the catalogue deliberately calls them
`map-cell-plane` rather than claiming they are live terrain. Each plane is
preserved and hashed separately.

### Labels, embedded text, and events

The next byte is a count followed by that many one-byte-length Shift-JIS
strings. They are character/speaker-style labels in story records. This is
followed by exactly 256 text slots, each encoded as a big-endian two-byte length
and Shift-JIS payload. Empty slots are legal.

The final section begins with a one-byte event count. Each event is:

```text
30 bytes    trigger/header data (field meanings not yet typed)
u16be       command count
commands    repeated command count times
```

Each command is `[opcode:u8][payload_size:u8][payload...]`. The parser
catalogues every nonempty text slot, event, and command with its original file
offset. Event-trigger fields, opcode meanings, and text references remain the
next semantic layer; structural decoding alone does not make a map record fully
understood.
