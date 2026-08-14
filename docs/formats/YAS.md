# YAS animation files

All 139 `.yas` files begin with `YAS\0` and a little-endian version value of 1.
The current decoder records eight 32-bit header words beginning at offset
`0x04`. It also conservatively reads the printable NUL-terminated string in the
`0x40..0x5f` header region as a texture filename.

Every file has a plausible texture name. Of the resulting references, 129
resolve directly to a texture beside the YAS file; these point to 93 unique
assets because animations reuse textures. The remaining names are retained but
not guessed to another path.

The complete field meanings and timeline/body layout remain unknown. The entry
confidence is therefore `probable` and `understood = 0`, despite the confirmed
magic, version, and file boundaries. The primary decoder anchor is
`yas::Animation::open(char const*)` at ARMv6 `0x7a05c` and ARMv7 `0x78804`.
Its associated `update`, `draw`, `play`, and texture-loading methods should make
the body format recoverable without inference from images alone.
