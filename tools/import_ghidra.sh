#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ghidra_dir="$repo_root/workspace/toolchains/ghidra_12.1.2_PUBLIC"
project_dir="$repo_root/workspace/ghidra"
import_dir="$project_dir/imports"
project_name="hrr-2.0.0"
default_executable="$repo_root/workspace/extracted/hills-and-rivers-remain-2.0.0/Payload/国破れて山河.app/国破れて山河"
executable="${1:-$default_executable}"

if [[ ! -x "$ghidra_dir/support/analyzeHeadless" ]]; then
    echo "Ghidra was not found: $ghidra_dir" >&2
    exit 1
fi

if [[ ! -f "$executable" ]]; then
    echo "game executable not found: $executable" >&2
    exit 1
fi

lipo="$(command -v llvm-lipo || command -v llvm-lipo-18)"
mkdir -p "$import_dir"

for architecture in armv6 armv7; do
    slice="$import_dir/hrr-2.0.0-$architecture"
    "$lipo" "$executable" -thin "$architecture" -output "$slice"
    chmod a-w "$slice"
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
        "$ghidra_dir/support/analyzeHeadless" \
        "$project_dir" "$project_name" \
        -import "$slice" -overwrite -analysisTimeoutPerFile 600
done
