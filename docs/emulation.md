# Linux execution baseline

## Confirmed result

The decrypted 2.0.0 ARMv7 executable boots in touchHLE on x86-64 Linux. With the
compatibility patch in `emulation/patches/`, it reaches and remains at the English
title screen, renders through OpenGL ES 1.1 at approximately 30 FPS, initializes
audio, and accepts touchHLE's normal input path.

This is already useful as a behavioral oracle. It is not yet a claim that every
scenario or game system works correctly.

Tested local baseline:

- touchHLE commit `331903de883405a8597036e4ed5ce8333f1604c9`
- Ghidra 12.1.2
- OpenJDK 21
- Mesa llvmpipe OpenGL 4.5 through Xvfb
- game bundle version 2.0.0, ARMv7 slice selected by touchHLE

## Required touchHLE compatibility

Unmodified touchHLE stops first at missing SystemConfiguration reachability
scheduling, then while parsing the app's region-qualified locale. The local
patch adds:

- successful no-op reachability callback/run-loop scheduling;
- parsing for locale IDs such as `en_US` and `en-US`;
- a deterministic fallback for `displayNameForKey:value:`.

The reachability callbacks do not currently fire. That is acceptable for title
screen boot, but network-dependent behavior must be catalogued and tested
separately.

## Running

Prepare the tested checkout from the repository root:

```sh
git clone https://github.com/touchHLE/touchHLE.git workspace/toolchains/touchHLE
git -C workspace/toolchains/touchHLE checkout 331903de883405a8597036e4ed5ce8333f1604c9
git -C workspace/toolchains/touchHLE apply ../../../emulation/patches/touchhle-hrr-bootstrap.patch
cargo build --release --manifest-path workspace/toolchains/touchHLE/Cargo.toml
```

Then run:

```sh
tools/run_touchhle.sh
```

When no display is present, the wrapper uses Xvfb. On a desktop it opens a normal
touchHLE window. The title screen may remain black briefly while startup and
audio initialization complete.

## Ghidra

The local ignored project is `workspace/ghidra/hrr-2.0.0`. Both ARM slices are
imported separately because importing the universal binary directly selects the
first (ARMv6) slice. Run `tools/import_ghidra.sh` after installing Ghidra under
`workspace/toolchains/ghidra_12.1.2_PUBLIC`.
