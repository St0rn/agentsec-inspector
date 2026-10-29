#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log build "$(basename -- "$0")"

for target in \
    "${REPO_ROOT}/backend/build" \
    "${REPO_ROOT}/backend/dist" \
    "${REPO_ROOT}/frontend/dist" \
    "${REPO_ROOT}/frontend/coverage" \
    "${REPO_ROOT}/src-tauri/target"; do
    [[ "${target}" == "${REPO_ROOT}/"* ]] || die "Refusing path outside the repository: ${target}"
    [[ -e "${target}" ]] && rm -rf -- "${target}"
done
find "${REPO_ROOT}" -type d -name '__pycache__' -prune -exec rm -rf -- {} +
log OK "Generated build and test artifacts removed. User data was not touched."
finish 0
