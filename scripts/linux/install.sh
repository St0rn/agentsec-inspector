#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log installation "$(basename -- "$0")"
assert_linux_x64

artifact=""
package_version="${AGENTSEC_VERSION}"
while (($#)); do
    case "$1" in
        --artifact) artifact="${2:-}"; shift 2 ;;
        --install-root) export AGENTSEC_INSTALL_ROOT="${2:-}"; shift 2 ;;
        --version) package_version="${2:-}"; shift 2 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
[[ "${package_version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Package version must use semantic versioning (for example 1.0.0)."

if [[ -z "${artifact}" ]]; then
    artifact="$(find "${REPO_ROOT}/src-tauri/target/release/bundle" -type f -name '*.AppImage' -print -quit 2>/dev/null || true)"
fi
[[ -n "${artifact}" && -f "${artifact}" ]] || die "AppImage not found. Pass --artifact or run build-linux.sh."
[[ "${artifact}" == *.AppImage ]] || die "The Linux user installer expects an AppImage artifact."

root="$(install_root)"
bin_dir="$(user_bin_dir)"
applications_dir="$(desktop_dir)"
app_path="${root}/agentsec-inspector.AppImage"
mkdir -p -- "${root}" "${bin_dir}" "${applications_dir}"

temporary="${root}/.agentsec-inspector.new"
install -m 0755 "${artifact}" "${temporary}"
mv -f -- "${temporary}" "${app_path}"
sha256sum "${app_path}" | awk '{print $1}' > "${root}/agentsec-inspector.sha256"
printf '%s\n' "${package_version}" > "${root}/VERSION"
ln -sfn -- "${app_path}" "${bin_dir}/agentsec-inspector"

desktop_file="${applications_dir}/agentsec-inspector.desktop"
{
    printf '%s\n' '[Desktop Entry]'
    printf '%s\n' 'Type=Application'
    printf '%s\n' 'Name=AgentSec Inspector'
    printf '%s\n' 'Comment=AI and MCP security auditing platform'
    printf 'Exec=%s\n' "${app_path}"
    printf '%s\n' 'Terminal=false'
    printf '%s\n' 'Categories=Development;Security;'
} > "${desktop_file}"
chmod 0644 "${desktop_file}"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${applications_dir}" >/dev/null 2>&1 || true
fi

log OK "Installed AgentSec Inspector ${package_version} at ${app_path}. Run agentsec-inspector from ${bin_dir}."
finish 0
