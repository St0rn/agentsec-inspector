#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log tests "$(basename -- "$0")"

root="$(install_root)"
app_path="${root}/agentsec-inspector.AppImage"
checksum_file="${root}/agentsec-inspector.sha256"
[[ -x "${app_path}" ]] || die "Installed AppImage is missing or not executable."
[[ -f "${checksum_file}" ]] || die "Installation checksum is missing."
expected="$(tr -d '[:space:]' < "${checksum_file}")"
actual="$(sha256sum "${app_path}" | awk '{print $1}')"
[[ "${actual}" == "${expected}" ]] || die "Installed AppImage checksum mismatch."
[[ -L "$(user_bin_dir)/agentsec-inspector" ]] || die "User command symlink is missing."

temporary_dir="$(mktemp -d -t agentsec-verify-XXXXXX)"
backend_pid=""
cleanup() {
    if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
        kill "${backend_pid}" 2>/dev/null || true
        wait "${backend_pid}" 2>/dev/null || true
    fi
    rm -rf -- "${temporary_dir}"
}
trap cleanup EXIT INT TERM

(cd "${temporary_dir}" && "${app_path}" --appimage-extract >/dev/null)
[[ -d "${temporary_dir}/squashfs-root" ]] || die "AppImage extraction failed or produced no filesystem."
extracted_backend="$(find "${temporary_dir}/squashfs-root" -type f -name 'agentsec-backend*' -perm -u+x -print -quit)"
[[ -n "${extracted_backend}" ]] || die "Bundled backend was not found in the AppImage."

port="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')"
token="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
test_data="${temporary_dir}/data"
mkdir -p -- "${test_data}"
AGENTSEC_DATA_DIR="${test_data}" AGENTSEC_API_TOKEN="${token}" AGENTSEC_PORT="${port}" "${extracted_backend}" &
backend_pid="$!"

healthy=false
for _ in {1..30}; do
    if curl --fail --silent "http://127.0.0.1:${port}/health" >/dev/null; then healthy=true; break; fi
    sleep 0.25
done
[[ "${healthy}" == true ]] || die "Bundled backend did not become healthy."
unauthorized="$(curl --silent --output /dev/null --write-out '%{http_code}' "http://127.0.0.1:${port}/api/v1/projects")"
[[ "${unauthorized}" == "401" ]] || die "Backend authentication check failed."

project_payload='{"client_name":"Installation verification","engagement_name":"Local smoke test","authorized_scope":"Temporary loopback test"}'
created="$(curl --fail --silent -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' -d "${project_payload}" "http://127.0.0.1:${port}/api/v1/projects")"
project_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "${created}")"
[[ -n "${project_id}" ]] || die "Project creation smoke test failed."
curl --fail --silent -H "Authorization: Bearer ${token}" "http://127.0.0.1:${port}/api/v1/projects/${project_id}" >/dev/null
[[ -f "${test_data}/agentsec.db" ]] || die "Database initialization check failed."
structured_log="${test_data}/logs/agentsec.jsonl"
[[ -s "${structured_log}" ]] || die "Structured logging check failed: agentsec.jsonl is missing or empty."
python3 - "${structured_log}" <<'PY' || die "Structured logging check failed: no backend_started JSON event."
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    events = []
    for line in handle:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
if not any(event.get("event") == "backend_started" for event in events):
    raise SystemExit(1)
PY

log OK "AppImage, checksum, bundled backend, authentication, database, API CRUD, and logging verified."
finish 0
