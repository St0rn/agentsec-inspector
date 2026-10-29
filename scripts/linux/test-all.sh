#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log tests "$(basename -- "$0")"

python_bin="$(venv_python)"
[[ -x "${python_bin}" ]] || die "Python environment missing. Run install-dev.sh first."

(cd "${REPO_ROOT}/backend" && "${python_bin}" -m ruff check agentsec tests ../demo)
(cd "${REPO_ROOT}/backend" && "${python_bin}" -m mypy agentsec)
(cd "${REPO_ROOT}/backend" && "${python_bin}" -m pytest --cov=agentsec --cov-report=term-missing --cov-report="json:${REPO_ROOT}/logs/tests/backend-coverage.json" --cov-fail-under=80)
npm --prefix "${REPO_ROOT}/frontend" run lint
npm --prefix "${REPO_ROOT}/frontend" test
npm --prefix "${REPO_ROOT}/frontend" run build
"${SCRIPT_DIR}/test-scripts.sh"
finish 0
