#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
touchhle_dir="$repo_root/workspace/toolchains/touchHLE"
touchhle_binary="$touchhle_dir/target/release/touchHLE"
default_app="$repo_root/workspace/extracted/hills-and-rivers-remain-2.0.0/Payload/国破れて山河.app"
app_path="$default_app"

if (($# > 0)) && [[ "$1" != --* ]]; then
    app_path="$1"
    shift
fi

window_scale="${HRR_WINDOW_SCALE:-${HRR_SCALE:-3}}"
render_scale="${HRR_RENDER_SCALE:-1}"
for setting in "HRR_WINDOW_SCALE=$window_scale" "HRR_RENDER_SCALE=$render_scale"; do
    value="${setting#*=}"
    if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
        echo "${setting%%=*} must be a positive integer: $value" >&2
        exit 1
    fi
done

touchhle_options=(
    --no-error-popup
    --print-fps
    "--scale-hack=$render_scale"
    "--window-scale=$window_scale"
)
if [[ "${HRR_FILTER:-nearest}" == nearest ]]; then
    touchhle_options+=(--nearest-neighbor)
elif [[ "${HRR_FILTER:-nearest}" != linear ]]; then
    echo "HRR_FILTER must be nearest or linear: ${HRR_FILTER}" >&2
    exit 1
fi
if [[ "${HRR_FULLSCREEN:-0}" == 1 ]]; then
    touchhle_options+=(--fullscreen)
fi
touchhle_options+=("$@")

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
    exec xvfb-run -a "$touchhle_binary" "$app_path" "${touchhle_options[@]}"
fi

exec "$touchhle_binary" "$app_path" "${touchhle_options[@]}"
