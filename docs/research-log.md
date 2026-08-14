# Research log

Use dated UTC entries. Preserve exact URLs, query terms, archive item names, and
negative results so searches are reproducible and do not needlessly repeat.

## 2026-08-14 — Repository initialized

- Created the private project scaffold.
- Seeded two reported filename leads in the variant ledger.
- No IPA has yet been acquired or analyzed in this repository.

## 2026-08-14 — First artifact acquired

- Found Archive.org items `HillsAndRiversRemain`, `Over700iOSGames`, and
  `Hills_and_Rivers_Remain_2.0.0_ios_3.0`.
- Their file metadata identifies the same byte-for-byte 2.0.0 IPA, so only one
  preserved copy was downloaded.
- Confirmed ARMv6 and ARMv7 slices and `cryptid 0` in both.
- Confirmed that local symbols survive and extracted 152 original object names.
- Indexed the current Grand IPA Archive/AppDrop catalogue (roughly 157,000
  version entries). It contains only this same 2.0.0 artifact for the bundle ID.
- Confirmed the Lite App Store ID as `338528080`; no Lite IPA appeared in that
  catalogue or Archive.org metadata search.
- Confirmed the 1.1.0 scene filename in a January 2010 IPA-pack index. Its ten
  RapidShare parts are no longer available and produced no usable Wayback
  captures in this pass.

## 2026-08-14 — Static and Linux execution baseline

- Installed Ghidra 12.1.2 with OpenJDK 21 and completed headless analysis of
  separate ARMv6 and ARMv7 programs in the ignored `hrr-2.0.0` project.
- Built touchHLE commit `331903de883405a8597036e4ed5ce8333f1604c9`
  locally on x86-64 Linux.
- The stock emulator reached game initialization but stopped at missing
  Reachability scheduling and region-qualified `NSLocale` behavior.
- Added three narrow compatibility shims and preserved them as a standalone
  patch. The original ARMv7 executable then reached the English title screen,
  initialized audio, and remained stable at approximately 30 FPS for the
  30-second test window.
- Added a normalized SQLite catalogue schema and builder. The first generated
  catalogue indexes 2 slices, 48 sections, 28 library references, 12,210 symbol
  records, 10 Objective-C classes, 216 methods, 88 fields, 152 object files, and
  2,342 non-executable bundle files.
