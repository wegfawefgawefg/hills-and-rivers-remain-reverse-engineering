# Hills and Rivers Remain Preservation

Preservation and clean-room reverse-engineering workspace for Square Enix's
32-bit iOS game *Hills and Rivers Remain* (circa 2009).

This repository tracks provenance, hashes, tooling, technical findings, and
eventually a native reimplementation or compatibility layer. Original IPAs,
decrypted executables, and extracted commercial assets are deliberately ignored
by Git, including in this private repository.

## Current phase

1. Locate and preserve every surviving IPA variant.
2. Hash and inventory each artifact without modifying the original.
3. Extract its app bundle and inspect its Mach-O executable.
4. Record architecture slices, deployment target, imports, and FairPlay
   `cryptid` status.
5. Prefer an already-decrypted executable before investing in old-device
   execution and memory dumping.
6. Import plaintext executables into Ghidra and map the engine from startup
   through rendering, input, data loading, entities, AI, saves, and audio.

## Workspace

```text
docs/                 Version ledger, findings, and research notes
tools/                Reproducible inspection helpers
workspace/originals/  Untouched acquired IPAs (ignored)
workspace/extracted/  One extracted tree per artifact (ignored)
workspace/reports/    Generated inventories and command output (ignored)
workspace/ghidra/     Local Ghidra projects (ignored)
```

Put each downloaded file in `workspace/originals/` and make it read-only. Run:

```bash
python3 tools/inventory_ipa.py workspace/originals/example.ipa \
  --extract workspace/extracted/example \
  --report workspace/reports/example.json
```

Then add its provenance and results to [`docs/variants.md`](docs/variants.md).
Never rename, recompress, patch, or overwrite the preserved source file.

## Scope and handling

The repository is for interoperability research, historical preservation, and
documentation. Do not commit or redistribute copyrighted game binaries or
assets. Record public source URLs and cryptographic hashes instead. Keep any
clean-room reimplementation separate from extracted code and assets as the
project matures.
