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
these are indexed game-data containers. The internal record schema is not yet
claimed; each record remains `understood = 0` until its consumer code proves
field meanings.

The ARMv6 pack consumer is `MapData::readPackData(int) const` at `0x6d6b8`; the
ARMv7 counterpart is at `0x6beec`. Both lead to
`FileManager::ReadBuffPackData(std::string const&, int, int)`.
