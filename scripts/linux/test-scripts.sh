#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log tests "$(basename -- "$0")"

temporary_root="$(mktemp -d -t agentsec-linux-scripts-XXXXXX)"
trap 'rm -rf -- "${temporary_root}"' EXIT
export HOME="${temporary_root}/home"
export XDG_DATA_HOME="${temporary_root}/xdg-data"
export XDG_BIN_HOME="${temporary_root}/bin"
export AGENTSEC_INSTALL_ROOT="${temporary_root}/application"
export AGENTSEC_DATA_DIR="${temporary_root}/user-data"
mkdir -p -- "${HOME}" "${AGENTSEC_DATA_DIR}/logs"

log INFO "Checking Bash syntax for every Linux lifecycle script."
while IFS= read -r -d '' script; do
    bash -n "${script}"
done < <(find "${SCRIPT_DIR}" -type f -name '*.sh' -print0)

python3 - "${AGENTSEC_DATA_DIR}/agentsec.db" <<'PY'
import sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
connection.execute("create table validation (value text not null)")
connection.execute("insert into validation values ('preserved')")
connection.commit()
connection.close()
PY
printf '%s\n' '{"event":"script-test"}' > "${AGENTSEC_DATA_DIR}/logs/agentsec.jsonl"

backup="${temporary_root}/backup.tar.gz"
"${SCRIPT_DIR}/backup.sh" "${backup}"
rm -f -- "${AGENTSEC_DATA_DIR}/agentsec.db"
set +e
"${SCRIPT_DIR}/restore.sh" "${backup}" >/dev/null 2>&1
restore_without_confirmation="$?"
set -e
[[ "${restore_without_confirmation}" -ne 0 ]] || die "Restore should require explicit confirmation."
"${SCRIPT_DIR}/restore.sh" "${backup}" --yes
[[ -f "${AGENTSEC_DATA_DIR}/agentsec.db" ]] || die "Restore did not recreate the database."

fixture="${temporary_root}/fixture.AppImage"
cp -- /bin/true "${fixture}"
chmod 0755 "${fixture}"
"${SCRIPT_DIR}/install.sh" --artifact "${fixture}" --version 2.0.0
first_checksum="$(cat "${AGENTSEC_INSTALL_ROOT}/agentsec-inspector.sha256")"
"${SCRIPT_DIR}/install.sh" --artifact "${fixture}" --version 2.0.0
[[ "$(cat "${AGENTSEC_INSTALL_ROOT}/agentsec-inspector.sha256")" == "${first_checksum}" ]] || die "Second installation changed the artifact."
"${SCRIPT_DIR}/update.sh" "${fixture}" 2.0.0

older_fixture="${temporary_root}/older.AppImage"
cp -- /bin/false "${older_fixture}"
chmod 0755 "${older_fixture}"
set +e
"${SCRIPT_DIR}/update.sh" "${older_fixture}" 1.0.0 >/dev/null 2>&1
downgrade_code="$?"
"${SCRIPT_DIR}/verify-installation.sh" >/dev/null 2>&1
invalid_artifact_code="$?"
"${SCRIPT_DIR}/uninstall.sh" --delete-data >/dev/null 2>&1
unconfirmed_delete_code="$?"
set -e
[[ "${downgrade_code}" -ne 0 ]] || die "Update should refuse a downgrade."
[[ "${invalid_artifact_code}" -ne 0 ]] || die "Verification should reject an invalid AppImage."
[[ "${unconfirmed_delete_code}" -ne 0 ]] || die "Data deletion should require confirmation."
[[ -d "${AGENTSEC_INSTALL_ROOT}" ]] || die "Unconfirmed uninstall unexpectedly removed the application."
"${SCRIPT_DIR}/uninstall.sh"
[[ -f "${AGENTSEC_DATA_DIR}/agentsec.db" ]] || die "Default uninstall should preserve user data."

"${SCRIPT_DIR}/install.sh" --artifact "${fixture}" --version 2.0.0
"${SCRIPT_DIR}/uninstall.sh" --delete-data --yes
[[ ! -e "${AGENTSEC_DATA_DIR}" ]] || die "Confirmed data deletion did not remove user data."

log OK "Syntax, backup, restore, idempotence, downgrade, verification, and uninstall error paths passed."
finish 0
