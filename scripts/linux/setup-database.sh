#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log installation "$(basename -- "$0")"

python_bin="$(venv_python)"
[[ -x "${python_bin}" ]] || die "Python environment missing. Run install-dev.sh first."
AGENTSEC_DATA_DIR="$(data_dir)"
export AGENTSEC_DATA_DIR
mkdir -p -- "${AGENTSEC_DATA_DIR}"
chmod 700 "${AGENTSEC_DATA_DIR}"

(cd "${REPO_ROOT}/backend" && "${python_bin}" -c 'from agentsec.database import migrate_db; from agentsec.main import seed_scenarios; migrate_db(); seed_scenarios(); print("database migrated")')
[[ -f "${AGENTSEC_DATA_DIR}/agentsec.db" ]] || die "Database file was not created."
finish 0
