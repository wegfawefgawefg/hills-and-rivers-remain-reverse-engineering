#!/usr/bin/env python3
"""Hash, safely extract, and inventory an iOS IPA using the Python stdlib."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import shutil
import stat
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLIST_KEYS = (
    "CFBundleIdentifier",
    "CFBundleExecutable",
    "CFBundleDisplayName",
    "CFBundleName",
    "CFBundleShortVersionString",
    "CFBundleVersion",
    "MinimumOSVersion",
    "DTPlatformVersion",
    "DTSDKName",
    "UIDeviceFamily",
    "UIRequiredDeviceCapabilities",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for member in archive.infolist():
        output = (destination / member.filename).resolve()
        if destination != output and destination not in output.parents:
            raise ValueError(f"unsafe archive member: {member.filename}")
        archive.extract(member, destination)


def json_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def command_output(arguments: list[str]) -> dict[str, Any]:
    executable = shutil.which(arguments[0])
    if executable is None:
        return {"available": False, "command": arguments}
    result = subprocess.run(
        [executable, *arguments[1:]],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "available": True,
        "command": arguments,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def make_read_only(path: Path) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def inspect_ipa(ipa_path: Path, extract_path: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "inspected_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(ipa_path.resolve()),
            "filename": ipa_path.name,
            "size_bytes": ipa_path.stat().st_size,
            "sha256": sha256_file(ipa_path),
        },
    }

    with zipfile.ZipFile(ipa_path) as archive:
        members = archive.infolist()
        result["archive"] = {
            "member_count": len(members),
            "uncompressed_size_bytes": sum(item.file_size for item in members),
            "members": [item.filename for item in members],
        }
        plist_names = [
            item.filename
            for item in members
            if item.filename.startswith("Payload/")
            and item.filename.count("/") == 2
            and item.filename.endswith(".app/Info.plist")
        ]
        if len(plist_names) != 1:
            result["error"] = f"expected one top-level app Info.plist, found {len(plist_names)}"
        else:
            plist_name = plist_names[0]
            plist = plistlib.loads(archive.read(plist_name))
            executable_name = plist.get("CFBundleExecutable")
            app_prefix = plist_name.removesuffix("Info.plist")
            executable_member = app_prefix + executable_name if executable_name else None
            result["bundle"] = {
                "path": app_prefix.rstrip("/"),
                "info_plist_path": plist_name,
                "info_plist": json_value(plist),
                "summary": {key: json_value(plist[key]) for key in PLIST_KEYS if key in plist},
                "executable_member": executable_member,
            }

        if extract_path is not None:
            safe_extract(archive, extract_path)
            result["extracted_to"] = str(extract_path.resolve())

    bundle = result.get("bundle")
    if extract_path is not None and bundle and bundle.get("executable_member"):
        executable = extract_path / bundle["executable_member"]
        if executable.is_file():
            result["executable"] = {
                "path": str(executable.resolve()),
                "size_bytes": executable.stat().st_size,
                "sha256": sha256_file(executable),
                "file": command_output(["file", str(executable)]),
            }

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path, help="untouched source IPA")
    parser.add_argument("--extract", type=Path, help="new extraction directory")
    parser.add_argument("--report", type=Path, help="JSON report path (default: stdout)")
    parser.add_argument(
        "--lock-original",
        action="store_true",
        help="remove write permission from the source IPA after hashing",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ipa_path = args.ipa.resolve()
    if not ipa_path.is_file():
        print(f"error: IPA does not exist: {ipa_path}", file=sys.stderr)
        return 2
    if args.extract and args.extract.exists() and any(args.extract.iterdir()):
        print(f"error: extraction directory is not empty: {args.extract}", file=sys.stderr)
        return 2

    try:
        report = inspect_ipa(ipa_path, args.extract)
    except (OSError, ValueError, zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.lock_original:
        make_read_only(ipa_path)

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
