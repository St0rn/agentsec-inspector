#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log installation "$(basename -- "$0")"

delete_data=false
confirmed=false
for argument in "$@"; do
    [[ "${argument}" == "--delete-data" ]] && delete_data=true
    [[ "${argument}" == "--yes" ]] && confirmed=true
done

if [[ "${delete_data}" == true && "${confirmed}" == false ]]; then
    die "Nothing was removed. Add --yes with --delete-data to confirm permanent data deletion."
fi

root="$(install_root)"
assert_safe_exact_dir "${root}" "$(install_root)"
rm -f -- "$(user_bin_dir)/agentsec-inspector" "$(desktop_dir)/agentsec-inspector.desktop"
if [[ -d "${root}" ]]; then
    rm -rf -- "${root}"
fi

if [[ "${delete_data}" == true ]]; then
    user_data="$(data_dir)"
    assert_safe_exact_dir "${user_data}" "$(data_dir)"
    [[ -d "${user_data}" ]] && rm -rf -- "${user_data}"
    log WARN "Application and user data were permanently removed."
else
    log OK "Application removed. Projects, evidence, and reports were preserved in $(data_dir)."
fi
finish 0
