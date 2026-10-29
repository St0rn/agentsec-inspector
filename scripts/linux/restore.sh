#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log updates "$(basename -- "$0")"

archive="${1:-}"
confirmation="${2:-}"
[[ -f "${archive}" ]] || die "Usage: restore.sh BACKUP.tar.gz --yes"
[[ "${confirmation}" == "--yes" ]] || die "Restore replaces the current data directory. Re-run with --yes after reviewing the backup."

if [[ -f "${archive}.sha256" ]]; then
    (cd "$(dirname -- "${archive}")" && sha256sum --check "$(basename -- "${archive}.sha256")")
fi
while IFS= read -r entry; do
    [[ "${entry}" != /* && "${entry}" != *"../"* ]] || die "Unsafe path in backup archive: ${entry}"
done < <(tar -tzf "${archive}")

target="$(data_dir)"
parent="$(dirname -- "${target}")"
temporary_dir="$(mktemp -d -p "${parent}" agentsec-restore-XXXXXX)"
trap '[[ -d "${temporary_dir}" ]] && rm -rf -- "${temporary_dir}"' EXIT
tar -xzf "${archive}" -C "${temporary_dir}"
[[ -f "${temporary_dir}/agentsec.db" ]] || die "Backup does not contain agentsec.db."
python3 - "${temporary_dir}/agentsec.db" <<'PY'
import sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
result = connection.execute("PRAGMA integrity_check").fetchone()[0]
connection.close()
raise SystemExit(0 if result == "ok" else 1)
PY

previous="${target}.before-restore-$(date -u +%Y%m%d-%H%M%S)"
if [[ -d "${target}" ]]; then
    mv -- "${target}" "${previous}"
fi
if ! mv -- "${temporary_dir}" "${target}"; then
    [[ -d "${previous}" ]] && mv -- "${previous}" "${target}"
    die "Restore failed; previous data was put back."
fi
chmod 700 "${target}"
log OK "Restore completed. Previous data preserved at ${previous}."
finish 0
