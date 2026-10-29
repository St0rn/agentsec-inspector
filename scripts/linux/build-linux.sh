#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

skip_tests=false
[[ "${1:-}" == "--skip-tests" ]] && skip_tests=true
init_log build "$(basename -- "$0")"
assert_linux_x64
"${SCRIPT_DIR}/check-prerequisites.sh" --build

if [[ "${skip_tests}" == false ]]; then
    "${SCRIPT_DIR}/test-all.sh"
fi

python_bin="$(venv_python)"
tauri_bin="${REPO_ROOT}/frontend/node_modules/.bin/tauri"
[[ -x "${python_bin}" ]] || die "Python environment missing. Run install-dev.sh first."
[[ -x "${tauri_bin}" ]] || die "Tauri CLI missing. Run install-dev.sh first."

npm --prefix "${REPO_ROOT}/frontend" run build
(cd "${REPO_ROOT}/backend" && "${python_bin}" -m PyInstaller --clean --noconfirm agentsec-backend.spec)
backend_binary="${REPO_ROOT}/backend/dist/agentsec-backend"
[[ -x "${backend_binary}" ]] || die "PyInstaller backend binary is missing."

rust_target="$(rustc -vV | awk '/^host:/ {print $2}')"
[[ "${rust_target}" == "x86_64-unknown-linux-gnu" ]] || die "Unsupported Rust host target: ${rust_target}"
mkdir -p -- "${REPO_ROOT}/src-tauri/binaries"
install -m 0755 "${backend_binary}" "${REPO_ROOT}/src-tauri/binaries/agentsec-backend-${rust_target}"

(cd "${REPO_ROOT}" && "${tauri_bin}" build --bundles deb,appimage)
bundle_root="${REPO_ROOT}/src-tauri/target/release/bundle"
mapfile -t artifacts < <(find "${bundle_root}" -type f \( -name '*.AppImage' -o -name '*.deb' \) -print | sort)
((${#artifacts[@]} > 0)) || die "No AppImage or DEB package was generated."

report="${REPO_ROOT}/logs/build/linux-build-report.txt"
{
    printf 'timestamp=%s\nversion=%s\ntarget=%s\nsuccess=true\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${AGENTSEC_VERSION}" "${rust_target}"
    for artifact in "${artifacts[@]}"; do
        printf 'artifact=%s bytes=%s sha256=%s\n' "${artifact}" "$(stat -c %s "${artifact}")" "$(sha256sum "${artifact}" | awk '{print $1}')"
    done
} > "${report}"
log OK "Linux packages generated under ${bundle_root}."
finish 0
