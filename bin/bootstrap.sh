#! /bin/sh

# shellcheck disable=SC2016

# Copyright 2026 Daniil Chistyakov 

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -eu

LOG_PAUSE_SECONDS=0.5

TIMESTAMP_TEMPLATE="+%Y-%m-%d %H:%M:%S"
DEFAULT_SALTBOX_DIR="${HOME}/saltbox"
SALTBOX_INSTALLER_URL=https://dev.saltbox.pro/saltbox/saltbox-compose/-/raw/dev/bin/install_saltbox.py

OVERCOMMIT_OPTION_VALUE='vm.overcommit_memory=1'
OVERCOMMIT_PROC_FILE=/proc/sys/vm/overcommit_memory
OVERCOMMIT_SYSCTL_FILE=/etc/sysctl.d/saltbox.conf

PYTHON_REQ_HINT="Install Python (see requirements in README)"
DOCKER_REQ_HINT="Install Docker Engine: https://docs.docker.com/engine/install/"
SUDO_REQ_HINT="Run as root, or install sudo, to configure 'vm.overcommit_memory'"

TITTLE='
   ####################################################
 ########################################################
##                                                      ##
##          Bootstrap Salt.Box installation             ##
##                                                      ##
 #######################################################
   ####################################################
'


log() {
  level="${1}"
  msg="${2:-}"
  pause="${3:-${LOG_PAUSE_SECONDS}}"

  timestamp=$(date "${TIMESTAMP_TEMPLATE}")

  output="[${timestamp}] [${level}] ${msg}\n"

  if [ "$level" = "INFO" ]; then
    printf "%b" "${output}"
  else
    printf "%b" "${output}" >&2
  fi

  if [ "${pause}" != "0" ]; then
    sleep "${pause}"
  fi
}


indent() {
  sed 's/^/\t│ /'
}


run_indented() {
  cmd_display="$*"

  border_char="─"
  width=80
  top_border=""
  i=0
  while [ "$i" -lt "$width" ]; do
    top_border="${top_border}${border_char}"
    i=$((i + 1))
  done

  printf "\t┌%s\n" "$top_border"
  printf "\t│ %s\n" "$cmd_display"
  printf "\t├%s\n" "$top_border"

  fifo=${TMPDIR:-/tmp}/run_indented.$$
  mkfifo "$fifo" || return 1

  indent <"$fifo" &
  indent_pid=$!

  "$@" >"$fifo" 2>&1
  exit_code=$?

  wait "$indent_pid"

  rm -f "$fifo"

  printf "\t└%s\n" "$top_border"

  return "$exit_code"
}


fail() {
  log "ERROR" "$1"
  exit 1
}


check_cmd() {
  cmd_req="${1}"
  hint="${2:-}"

  if ! run_indented command -v "${cmd_req}"; then
    base_log_msg="'${cmd_req}' not found."
    if [ -n "${hint}" ]; then
      fail "${base_log_msg} ${hint}"
    else
      fail "${base_log_msg}"
    fi
  fi
  log "INFO" "Found '${cmd_req}' requirement"
}


check_reqs() {
  log "INFO" "Checking requirements..."

  check_cmd curl
  check_cmd python3 "${PYTHON_REQ_HINT}"
  check_cmd docker "${DOCKER_REQ_HINT}"

  log "INFO" "All requirements successfully found!"
}


set_overcommit() {
  log "INFO" "Setting 'vm.overcommit_memory=1'..."

  if ! as_root sh -c "printf '%s\n' '${OVERCOMMIT_OPTION_VALUE}' > '${OVERCOMMIT_SYSCTL_FILE}'"; then
    fail "Failed to set '${OVERCOMMIT_OPTION_VALUE}'"
  fi
  log "INFO" "Enabling '${OVERCOMMIT_OPTION_VALUE}' option now"

  if ! run_indented as_root sysctl -p "${OVERCOMMIT_SYSCTL_FILE}"; then
    fail "Failed to enable '${OVERCOMMIT_OPTION_VALUE}' option"
  fi
}


ensure_overcommit() {
  log "INFO" "Checking '${OVERCOMMIT_OPTION_VALUE%??}' option"

  current_status=$(cat "${OVERCOMMIT_PROC_FILE}" || echo "0")
  run_indented cat "${OVERCOMMIT_PROC_FILE}"

  if [ "${current_status}" = "1" ]; then
    log "INFO" "Option '${OVERCOMMIT_OPTION_VALUE%??}' is already set to '1'"
    return 0
  fi
  set_overcommit
}

_saltbox_dir="${SALTBOX_INSTALL_DIR:-${DEFAULT_SALTBOX_DIR}}"
prepare_workdir() {

  if [ -e "${_saltbox_dir}" ]; then
    if [ ! -d "${_saltbox_dir}" ]; then
      fail "Entity '${_saltbox_dir}' exists and is not a directory"
    fi
    if [ -n "$(ls -A "${_saltbox_dir}" 2>/dev/null)" ]; then
      run_indented ls -A "${_saltbox_dir}"
      fail "Working dir '${_saltbox_dir}' already exists and is not empty. Remove it or set 'SALTBOX_INSTALL_DIR' env to another path"
    fi
  else
    log "INFO" "Creating working directory"
    run_indented mkdir -vp "${_saltbox_dir}"
  fi
  log "INFO" "Using working directory: ${_saltbox_dir}"
}


install_saltbox() {

  if ! run_indented cd "${_saltbox_dir}"; then
    fail "Failed to change the current directory on '${_saltbox_dir}'"
  fi
  log "INFO" "Downloading 'install_saltbox.py' from ${SALTBOX_INSTALLER_URL}"

  if ! run_indented curl -fsSL "$SALTBOX_INSTALLER_URL" -o install_saltbox.py; then
    fail "Failed to download 'install_saltbox.py'"
  fi

  if ! python3 install_saltbox.py --compose-ref=RELEASE --non-interactive "$@"; then
    fail "Failed to run 'install_saltbox.py'"
  fi
}


as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    check_cmd sudo "${SUDO_REQ_HINT}"
    sudo "$@"
  fi
}


display_tittle() {
  printf "%s\n\n" "${TITTLE}"
}


main() {
  display_tittle
  check_reqs
  ensure_overcommit
  prepare_workdir
  install_saltbox "${@}"
}

main "${@}"
