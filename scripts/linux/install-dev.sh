#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

skip_check=false
[[ "${1:-}" == "--skip-prerequisite-check" ]] && skip_check=true
init_log installation "$(basename -- "$0")"
assert_linux_x64

if [[ "${skip_check}" == false ]]; then
    "${SCRIPT_DIR}/check-prerequisites.sh" --build
fi

if [[ ! -x "$(venv_python)" ]]; then
    log INFO "Creating isolated Python environment."
    python3 -m venv "${REPO_ROOT}/.venv"
fi

log INFO "Installing locked Python dependencies."
"$(venv_python)" -m pip install --disable-pip-version-check -r "${REPO_ROOT}/backend/requirements.lock"
log INFO "Installing locked frontend dependencies."
npm --prefix "${REPO_ROOT}/frontend" ci --no-audit --no-fund
"${SCRIPT_DIR}/setup-database.sh"
log OK "Linux development environment is ready."
finish 0
