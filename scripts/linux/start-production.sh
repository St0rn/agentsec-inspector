#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
init_log installation "$(basename -- "$0")"

app_path="$(install_root)/agentsec-inspector.AppImage"
[[ -x "${app_path}" ]] || die "AgentSec Inspector is not installed. Run install.sh first."
log INFO "Starting AgentSec Inspector."
exec "${app_path}"
