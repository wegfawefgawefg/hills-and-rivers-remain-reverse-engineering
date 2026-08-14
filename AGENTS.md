# Repository instructions

- Preserve acquired files byte-for-byte under `workspace/originals/`; never edit
  them in place.
- Do not commit IPAs, app bundles, executables, game assets, Ghidra databases, or
  credentials.
- Every artifact must have a source URL, acquisition timestamp, original
  filename, byte size, and SHA-256 recorded in `docs/variants.md`.
- Distinguish FairPlay encryption from control-flow or decompiler quality.
- Treat `cryptid = 0` as plaintext and `cryptid = 1` as encrypted, while
  recording the exact load command and slice inspected.
- Prefer small, reproducible tools whose output can be checked into `docs/` when
  it contains no copyrighted payload.
- Keep reverse-engineering observations evidence-based: include addresses,
  selectors, filenames, or command output sufficient to reproduce a claim.
