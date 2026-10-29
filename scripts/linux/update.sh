#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log updates "$(basename -- "$0")"

artifact="${1:-}"
new_version="${2:-${AGENTSEC_VERSION}}"
[[ -f "${artifact}" && "${artifact}" == *.AppImage ]] || die "Usage: update.sh NEW_VERSION.AppImage [SEMANTIC_VERSION]"
[[ "${new_version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "New version must use semantic versioning."
root="$(install_root)"
current="${root}/agentsec-inspector.AppImage"
[[ -x "${current}" ]] || die "Current installation not found. Use install.sh for the first installation."
current_version="$(cat "${root}/VERSION" 2>/dev/null || printf '0.0.0')"
if [[ "$(printf '%s\n%s\n' "${new_version}" "${current_version}" | sort -V | head -n1)" == "${new_version}" && "${new_version}" != "${current_version}" ]]; then
    die "Refusing downgrade from ${current_version} to ${new_version}."
fi
new_sha="$(sha256sum "${artifact}" | awk '{print $1}')"
current_sha="$(sha256sum "${current}" | awk '{print $1}')"
if [[ "${new_version}" == "${current_version}" && "${new_sha}" == "${current_sha}" ]]; then
    log OK "Version ${new_version} is already installed with the same checksum."
    finish 0
fi

"${SCRIPT_DIR}/backup.sh"
rollback="${root}/agentsec-inspector.rollback.AppImage"
cp -p -- "${current}" "${rollback}"

if "${SCRIPT_DIR}/install.sh" --artifact "${artifact}" --version "${new_version}" && "${SCRIPT_DIR}/verify-installation.sh"; then
    rm -f -- "${rollback}"
    log OK "Update completed and verified."
    finish 0
fi

log ERROR "Update verification failed; restoring the previous application."
mv -f -- "${rollback}" "${current}"
sha256sum "${current}" | awk '{print $1}' > "${root}/agentsec-inspector.sha256"
printf '%s\n' "${current_version}" > "${root}/VERSION"
finish 1
