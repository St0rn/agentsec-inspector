#!/usr/bin/env bash

set -Eeuo pipefail

readonly AGENTSEC_VERSION="1.0.0"
LINUX_LIB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly LINUX_LIB_DIR
REPO_ROOT="$(cd -- "${LINUX_LIB_DIR}/../../.." && pwd -P)"
readonly REPO_ROOT
LOG_FILE=""

init_log() {
    local category="$1" script_name="$2" timestamp
    timestamp="$(date -u +%Y%m%d-%H%M%S)"
    mkdir -p -- "${REPO_ROOT}/logs/${category}"
    LOG_FILE="${REPO_ROOT}/logs/${category}/${script_name%.sh}-${timestamp}.log"
    exec > >(tee -a "${LOG_FILE}") 2>&1
    log INFO "START | ${script_name} | AgentSec ${AGENTSEC_VERSION}"
}

log() {
    local level="$1"
    shift
    printf '%s | %s | %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${level}" "$*"
}

die() {
    log ERROR "$*"
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

data_dir() {
    if [[ -n "${AGENTSEC_DATA_DIR:-}" ]]; then
        printf '%s\n' "${AGENTSEC_DATA_DIR}"
    else
        printf '%s\n' "${XDG_DATA_HOME:-${HOME}/.local/share}/agentsec-inspector"
    fi
}

install_root() {
    printf '%s\n' "${AGENTSEC_INSTALL_ROOT:-${HOME}/.local/lib/agentsec-inspector}"
}

user_bin_dir() {
    printf '%s\n' "${XDG_BIN_HOME:-${HOME}/.local/bin}"
}

desktop_dir() {
    printf '%s\n' "${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
}

venv_python() {
    printf '%s\n' "${REPO_ROOT}/.venv/bin/python"
}

assert_linux_x64() {
    [[ "$(uname -s)" == "Linux" ]] || die "This script requires Linux."
    [[ "$(uname -m)" == "x86_64" ]] || die "V1 packages currently support Linux x86_64 only."
}

assert_safe_exact_dir() {
    local candidate="$1" allowed="$2" resolved_candidate resolved_allowed
    resolved_candidate="$(realpath -m -- "${candidate}")"
    resolved_allowed="$(realpath -m -- "${allowed}")"
    [[ "${resolved_candidate}" == "${resolved_allowed}" ]] || die "Refusing unexpected path: ${resolved_candidate}"
    [[ "${resolved_candidate}" != "/" && "${resolved_candidate}" != "${HOME}" ]] || die "Refusing broad destructive path."
}

finish() {
    local code="$1"
    if [[ "${code}" -eq 0 ]]; then
        log OK "END | exit_code=0"
    else
        log ERROR "END | exit_code=${code}"
    fi
    exit "${code}"
}
