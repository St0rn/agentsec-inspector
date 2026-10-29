#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

build=false
[[ "${1:-}" == "--build" ]] && build=true
init_log installation "$(basename -- "$0")"
assert_linux_x64

missing=()
for command_name in python3 node npm curl; do
    command -v "${command_name}" >/dev/null 2>&1 || missing+=("${command_name}")
done

if ((${#missing[@]})); then
    log ERROR "Missing commands: ${missing[*]}"
    log INFO "Install them with your distribution package manager; this script never installs system packages silently."
    finish 1
fi

python_version="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
node_version="$(node --version | sed 's/^v//')"
log INFO "Linux=$(uname -sr) architecture=$(uname -m)"
log INFO "Python=${python_version} Node.js=${node_version} npm=$(npm --version)"

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || die "Python 3.12 or newer is required."
node_major="${node_version%%.*}"
[[ "${node_major}" =~ ^[0-9]+$ && "${node_major}" -ge 22 ]] || die "Node.js 22 or newer is required."

if [[ "${build}" == true ]]; then
    for command_name in rustc cargo pkg-config gcc; do
        command -v "${command_name}" >/dev/null 2>&1 || missing+=("${command_name}")
    done
    for package_name in webkit2gtk-4.1 javascriptcoregtk-4.1 gtk+-3.0 libsoup-3.0; do
        pkg-config --exists "${package_name}" 2>/dev/null || missing+=("pkg-config:${package_name}")
    done
    if ((${#missing[@]})); then
        log ERROR "Missing Linux desktop build dependencies: ${missing[*]}"
        log INFO "Debian/Ubuntu packages: build-essential libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf libssl-dev libgtk-3-dev libsoup-3.0-dev"
        finish 1
    fi
    log INFO "Rust=$(rustc --version) Cargo=$(cargo --version)"
fi

finish 0
