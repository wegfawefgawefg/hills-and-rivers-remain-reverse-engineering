#!/usr/bin/env python3
"""Build a reproducible SQLite catalogue from an extracted iOS app bundle."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import plistlib
import re
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any


OBJECT_FILE_PATTERN = re.compile(r"(?:^|/)([^/\x00]+\.o)$")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def run_json(command: list[str]) -> dict[str, Any]:
    return json.loads(run(command))


def find_lipo() -> str:
    for candidate in ("llvm-lipo", "llvm-lipo-18", "llvm-lipo-17"):
        path = shutil.which(candidate)
        if path:
            return path
    raise RuntimeError("llvm-lipo was not found")


def architectures(executable: Path, lipo: str) -> list[str]:
    output = run([lipo, "-archs", str(executable)])
    result = output.strip().split()
    if not result:
        raise RuntimeError("the executable contains no detectable architectures")
    return result


def thin_slice(executable: Path, architecture: str, output: Path, lipo: str) -> None:
    subprocess.run(
        [lipo, str(executable), "-thin", architecture, "-output", str(output)],
        check=True,
    )


def cryptid(executable: Path) -> int:
    output = run(["llvm-objdump", "--macho", "--private-headers", str(executable)])
    match = re.search(r"^\s*cryptid\s+(\d+)\s*$", output, re.MULTILINE)
    if not match:
        raise RuntimeError(f"LC_ENCRYPTION_INFO not found in {executable}")
    return int(match.group(1))


def reset_build(connection: sqlite3.Connection, build_id: str) -> None:
    tables = (
        "observations",
        "resources",
        "object_files",
        "objc_fields",
        "objc_methods",
        "objc_classes",
        "symbols",
        "libraries",
        "sections",
        "slices",
        "builds",
    )
    for table in tables:
        key = "id" if table == "builds" else "build_id"
        connection.execute(f"DELETE FROM {table} WHERE {key} = ?", (build_id,))


def insert_build(
    connection: sqlite3.Connection,
    build_id: str,
    app: Path,
    executable: Path,
    info: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO builds (
            id, bundle_id, version, executable_name, minimum_os, app_path,
            executable_size, executable_sha256, catalogued_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            build_id,
            info.get("CFBundleIdentifier", ""),
            str(info.get("CFBundleShortVersionString", info.get("CFBundleVersion", ""))),
            info["CFBundleExecutable"],
            info.get("MinimumOSVersion"),
            str(app.resolve()),
            executable.stat().st_size,
            hash_file(executable),
            dt.datetime.now(dt.timezone.utc).isoformat(),
        ),
    )


def insert_slice(
    connection: sqlite3.Connection,
    build_id: str,
    architecture: str,
    executable: Path,
) -> None:
    info = run_json(["rabin2", "-j", "-I", str(executable)])["info"]
    connection.execute(
        """
        INSERT INTO slices (
            build_id, architecture, machine, bits, size, sha256, encrypted, stripped
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            build_id,
            architecture,
            info.get("machine"),
            info["bits"],
            executable.stat().st_size,
            hash_file(executable),
            int(cryptid(executable) != 0),
            int(info.get("stripped", False)),
        ),
    )

    section_rows = []
    for section in run_json(["rabin2", "-j", "-S", str(executable)]).get("sections", []):
        section_rows.append(
            (
                build_id,
                architecture,
                section["name"],
                section.get("vaddr", 0),
                section.get("paddr", 0),
                section.get("size", 0),
                section.get("perm"),
            )
        )
    connection.executemany(
        "INSERT INTO sections VALUES (?, ?, ?, ?, ?, ?, ?)", section_rows
    )

    libraries = run_json(["rabin2", "-j", "-l", str(executable)]).get("libs", [])
    connection.executemany(
        "INSERT INTO libraries VALUES (?, ?, ?)",
        ((build_id, architecture, library) for library in libraries),
    )

    symbol_rows = []
    for symbol in run_json(["rabin2", "-j", "-s", str(executable)]).get("symbols", []):
        symbol_rows.append(
            (
                build_id,
                architecture,
                symbol["ordinal"],
                symbol["name"],
                symbol.get("demname"),
                symbol.get("bind"),
                symbol.get("type"),
                symbol.get("vaddr"),
                symbol.get("paddr"),
                symbol.get("size"),
                int(symbol.get("is_imported", False)),
            )
        )
    connection.executemany(
        "INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", symbol_rows
    )

    class_rows = []
    method_rows = []
    field_rows = []
    classes = run_json(["rabin2", "-j", "-c", str(executable)]).get("classes", [])
    for objc_class in classes:
        class_name = objc_class["classname"]
        class_rows.append(
            (
                build_id,
                architecture,
                class_name,
                objc_class.get("super"),
                objc_class.get("addr"),
            )
        )
        for method in objc_class.get("methods", []):
            method_rows.append(
                (
                    build_id,
                    architecture,
                    class_name,
                    method["name"],
                    method.get("addr"),
                    int("class" in method.get("flags", [])),
                )
            )
        for field in objc_class.get("fields", []):
            field_rows.append(
                (
                    build_id,
                    architecture,
                    class_name,
                    field["name"],
                    field.get("addr"),
                )
            )
    connection.executemany(
        "INSERT INTO objc_classes VALUES (?, ?, ?, ?, ?)", class_rows
    )
    connection.executemany(
        "INSERT INTO objc_methods VALUES (?, ?, ?, ?, ?, ?)", method_rows
    )
    connection.executemany(
        "INSERT INTO objc_fields VALUES (?, ?, ?, ?, ?)", field_rows
    )


def insert_object_files(
    connection: sqlite3.Connection, build_id: str, executable: Path
) -> None:
    output = run(["strings", "-a", str(executable)])
    names = set()
    for line in output.splitlines():
        match = OBJECT_FILE_PATTERN.search(line.strip())
        if match:
            names.add(match.group(1))
    connection.executemany(
        "INSERT INTO object_files VALUES (?, ?)",
        ((build_id, name) for name in sorted(names)),
    )


def insert_resources(
    connection: sqlite3.Connection,
    build_id: str,
    app: Path,
    executable: Path,
) -> None:
    rows = []
    for path in sorted(app.rglob("*")):
        if not path.is_file() or path == executable:
            continue
        relative_path = path.relative_to(app).as_posix()
        extension = path.suffix.lower().lstrip(".")
        rows.append(
            (build_id, relative_path, extension, path.stat().st_size, hash_file(path))
        )
    connection.executemany("INSERT INTO resources VALUES (?, ?, ?, ?, ?)", rows)


def print_summary(connection: sqlite3.Connection, build_id: str, database: Path) -> None:
    print(f"Catalogue: {database}")
    for table in (
        "slices",
        "sections",
        "libraries",
        "symbols",
        "objc_classes",
        "objc_methods",
        "objc_fields",
        "object_files",
        "resources",
    ):
        count = connection.execute(
            f"SELECT count(*) FROM {table} WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        print(f"{table}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path, help="extracted .app directory")
    parser.add_argument("database", type=Path, help="output SQLite database")
    parser.add_argument("--build-id", required=True)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "catalog" / "schema.sql",
    )
    args = parser.parse_args()

    app = args.app.resolve()
    with (app / "Info.plist").open("rb") as plist_file:
        info = plistlib.load(plist_file)
    executable = app / info["CFBundleExecutable"]
    if not executable.is_file():
        raise SystemExit(f"executable not found: {executable}")

    args.database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(args.database)
    connection.executescript(args.schema.read_text(encoding="utf-8"))

    with connection:
        reset_build(connection, args.build_id)
        insert_build(connection, args.build_id, app, executable, info)
        lipo = find_lipo()
        with tempfile.TemporaryDirectory(prefix="hrr-catalog-") as temp_directory:
            for architecture in architectures(executable, lipo):
                thin = Path(temp_directory) / f"executable-{architecture}"
                thin_slice(executable, architecture, thin, lipo)
                insert_slice(connection, args.build_id, architecture, thin)
        insert_object_files(connection, args.build_id, executable)
        insert_resources(connection, args.build_id, app, executable)

    print_summary(connection, args.build_id, args.database)
    connection.close()


if __name__ == "__main__":
    main()
