#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log updates "$(basename -- "$0")"

source_dir="$(data_dir)"
[[ -d "${source_dir}" ]] || die "AgentSec data directory does not exist: ${source_dir}"
destination="${1:-${source_dir}/backups/agentsec-backup-$(date -u +%Y%m%d-%H%M%S).tar.gz}"
mkdir -p -- "$(dirname -- "${destination}")"

temporary_dir="$(mktemp -d -t agentsec-backup-XXXXXX)"
trap 'rm -rf -- "${temporary_dir}"' EXIT
mkdir -p -- "${temporary_dir}/payload"

while IFS= read -r -d '' item; do
    relative="${item#${source_dir}/}"
    [[ "${relative}" == backups/* ]] && continue
    if [[ "${relative}" == "agentsec.db" ]]; then
        python3 - "${item}" "${temporary_dir}/payload/agentsec.db" <<'PY'
import sqlite3, sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
target.close()
source.close()
PY
    elif [[ -f "${item}" ]]; then
        mkdir -p -- "${temporary_dir}/payload/$(dirname -- "${relative}")"
        cp -p -- "${item}" "${temporary_dir}/payload/${relative}"
    fi
done < <(find "${source_dir}" -type f -print0)

tar -C "${temporary_dir}/payload" -czf "${destination}" .
sha256sum "${destination}" > "${destination}.sha256"
log OK "Backup created: ${destination}"
finish 0
