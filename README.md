# Hills and Rivers Remain Reverse Engineering

Reverse-engineering and preservation workspace for Square Enix's 32-bit iOS
game *Hills and Rivers Remain* (circa 2009).

This repository tracks provenance, hashes, tooling, technical findings, and
eventually a native reimplementation or compatibility layer. Original IPAs,
decrypted executables, and extracted commercial assets are deliberately ignored
by Git, including in this private repository.

## Current phase

The surviving 2.0.0 build is decrypted, unstripped, imported into Ghidra, and
booting to its title screen in touchHLE on Linux. The active work is now a full
catalogue of binary structure, content formats, and observed behavior while the
search for older, Lite, and encrypted builds continues.

See [`docs/catalogue-plan.md`](docs/catalogue-plan.md) for the completeness
criteria, [`docs/coverage-matrix.md`](docs/coverage-matrix.md) for the living RE
queue, [`docs/emulation.md`](docs/emulation.md) for the Linux baseline, and
[`docs/remaster-notes.md`](docs/remaster-notes.md) for redesign observations
kept separate from preservation findings.

## Workspace

```text
docs/                 Version ledger, findings, and research notes
tools/                Reproducible inspection helpers
catalog/              Catalogue schema and evidence conventions
emulation/patches/    Reproducible compatibility patches
workspace/originals/  Untouched acquired IPAs (ignored)
workspace/extracted/  One extracted tree per artifact (ignored)
workspace/reports/    Generated inventories and command output (ignored)
workspace/ghidra/     Local Ghidra projects (ignored)
workspace/catalog/    Generated SQLite catalogues (ignored)
workspace/toolchains/ Local Ghidra/touchHLE checkouts (ignored)
```

Put each downloaded file in `workspace/originals/` and make it read-only. Run:

```bash
python3 tools/inventory_ipa.py workspace/originals/example.ipa \
  --extract workspace/extracted/example \
  --report workspace/reports/example.json
```

Then add its provenance and results to [`docs/variants.md`](docs/variants.md).
Never rename, recompress, patch, or overwrite the preserved source file.

Generate the mechanical and first-pass functional catalogue for an extracted
app with:

```bash
python3 tools/build_catalog.py \
  'workspace/extracted/example/Payload/Game.app' \
  workspace/catalog/example.sqlite \
  --build-id example
```

The builder strictly decodes complete map-record structure, localization
tables, and YAS animation headers. See
[`docs/functional-catalogue.md`](docs/functional-catalogue.md),
[`docs/gameplay-core.md`](docs/gameplay-core.md),
and [`docs/formats/`](docs/formats/) for current coverage and format evidence.

Export all 78 maps—including graph layouts, item slots, embedded text, events,
and raw opcode payloads—to inspectable JSON with:

```bash
python3 tools/export_maps.py \
  'workspace/extracted/example/Payload/Game.app' \
  workspace/catalog/example-maps.json
```

## Reproducibility boundary

The repeatable pipeline is retained in the repository rather than existing only
as terminal history:

- `tools/inventory_ipa.py` hashes, safely extracts, inventories, and optionally
  locks an untouched IPA; it records the plist and executable inspection output
  in JSON.
- `tools/build_catalog.py` rebuilds the SQLite inventory of Mach-O slices,
  sections, libraries, symbols, Objective-C metadata, object filenames,
  resources, localization, maps, events, commands, and YAS headers.
- `tools/export_maps.py` emits all structurally decoded map content as JSON.
- `tools/import_ghidra.sh` splits ARMv6/ARMv7 and performs headless Ghidra
  imports; the scripts under `tools/ghidra/` reproducibly decompile or
  disassemble selected addresses.
- `emulation/patches/` plus `tools/run_touchhle.sh` preserve and run the Linux
  compatibility setup.
- `tools/test_content_catalog.py` checks the strict content decoders.

The internet search/acquisition history, installation of external toolchains,
interactive game navigation, and semantic interpretation of decompiled
functions remain documented research procedures rather than one-command
automation. Generated reports, catalogues, extracted assets, and Ghidra project
databases stay ignored; they can be regenerated locally when the original IPA
and required tools are present.

## Scope and handling

The repository is for interoperability research, historical preservation, and
documentation. Do not commit or redistribute copyrighted game binaries or
assets. Record public source URLs and cryptographic hashes instead. Keep any
clean-room reimplementation separate from extracted code and assets as the
project matures.
