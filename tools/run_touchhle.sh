#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
touchhle_dir="$repo_root/workspace/toolchains/touchHLE"
touchhle_binary="$touchhle_dir/target/release/touchHLE"
default_app="$repo_root/workspace/extracted/hills-and-rivers-remain-2.0.0/Payload/国破れて山河.app"
app_path="${1:-$default_app}"

if [[ ! -x "$touchhle_binary" ]]; then
    echo "touchHLE is not built: $touchhle_binary" >&2
    exit 1
fi

if [[ ! -d "$app_path" ]]; then
    echo "app bundle not found: $app_path" >&2
    exit 1
fi

cd "$touchhle_dir"
if [[ -z "${DISPLAY:-}" ]]; then
    exec xvfb-run -a "$touchhle_binary" "$app_path" --no-error-popup --print-fps
fi

exec "$touchhle_binary" "$app_path" --no-error-popup --print-fps
