# IPA variant ledger

Add one section per distinct SHA-256. Claims from filenames or archive metadata
must be marked as claims until confirmed by `Info.plist` or executable evidence.

## Candidate leads

| Claimed filename | Claimed version | Source/status | SHA-256 |
| --- | --- | --- | --- |
| `Hills and Rivers Remain.ipa` | 2.0.0 | Acquired and verified | `b3b798103383f5b2b051ac47631f987cc7d2a438e3e0a8913eb5a8406a754015` |
| `Hills and Rivers Remain 1.1.0-H.ipa` | 1.1.0 | Scene-style release lead; not yet acquired | Pending |

## Verified artifacts

### `Hills and Rivers Remain.ipa`

- Source item: https://archive.org/details/HillsAndRiversRemain
- Additional byte-identical source item: https://archive.org/details/Over700iOSGames
- Duplicate renamed source item: https://archive.org/details/Hills_and_Rivers_Remain_2.0.0_ios_3.0
- Public archive date: 2018-08-24
- Acquired at (UTC): 2026-08-14T08:15:53Z
- Original filename: `Hills and Rivers Remain.ipa`
- Size (bytes): 105,046,051
- MD5: `c8bb87a5e3ecb8fb15e1ccfe051b974e`
- SHA-1: `d6dadf1c1eaa237bf8429404457f57b1fe7e8eec`
- SHA-256: `b3b798103383f5b2b051ac47631f987cc7d2a438e3e0a8913eb5a8406a754015`
- Bundle path: `Payload/国破れて山河.app`
- Bundle identifier: `com.square-enix.HillsAndRiversRemain`
- Executable: `国破れて山河`
- Executable size (bytes): 4,047,536
- Executable SHA-256: `fd922082187a435164d9eefb453f1197a68e59f063d83900e2354645dc09e0de`
- `CFBundleVersion`: `2.0.0`
- `CFBundleShortVersionString`: absent
- `MinimumOSVersion`: `3.0`
- Build SDK: iPhoneOS 4.3
- Device family: iPhone/iPod touch (`1`)
- Architecture slices: ARMv6 and ARMv7, both 32-bit little-endian Mach-O
- ARMv6 encryption: `LC_ENCRYPTION_INFO`, `cryptid 0`
- ARMv7 encryption: `LC_ENCRYPTION_INFO`, `cryptid 0`
- Assessment: already decrypted/plaintext and directly suitable for static RE
- Packaging note: `iTunesMetadata.plist` identifies scene account
  `drmVersionNumber = 0`, App Store item `334825813`,
  and eleven historical external version identifiers. The executable is reported
  as unstripped and retains extensive local C++ symbol and object-file metadata.

The three Archive.org items above expose the same 105,046,051-byte file with the
same MD5 and SHA-1. They are multiple provenance records, not distinct variants.

## Artifact template

### `<original filename>`

- Source URL:
- Source collection/uploader:
- Acquired at (UTC):
- Original filename:
- Size (bytes):
- SHA-256:
- Claimed release/version/date:
- Archive notes:
- Bundle path:
- Bundle identifier:
- Executable:
- `CFBundleShortVersionString`:
- `CFBundleVersion`:
- `MinimumOSVersion`:
- Architecture slices:
- Encryption load command / `cryptid` per slice:
- Assessment:
