#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log tests "$(basename -- "$0")"

port="${AGENTSEC_PORT:-8765}"
python_bin="$(venv_python)"
[[ -x "${python_bin}" ]] || die "Python environment missing. Run install-dev.sh first."
export AGENTSEC_API_TOKEN="${AGENTSEC_API_TOKEN:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"
export AGENTSEC_PORT="${port}"
export VITE_API_TOKEN="${AGENTSEC_API_TOKEN}"
export VITE_API_URL="http://127.0.0.1:${port}"

backend_pid=""
cleanup() {
    if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
        kill "${backend_pid}" 2>/dev/null || true
        wait "${backend_pid}" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

(cd "${REPO_ROOT}" && "${python_bin}" -m uvicorn agentsec.main:app --app-dir backend --host 127.0.0.1 --port "${port}") &
backend_pid="$!"
log INFO "Backend started on http://127.0.0.1:${port}; starting the frontend."
npm --prefix "${REPO_ROOT}/frontend" run dev
