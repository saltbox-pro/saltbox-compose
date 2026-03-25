#! /bin/bash

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [healthcheck ] ${*}"
}

run_check() {
  local name="$1"
  shift
  log "Running: ${name}"

  output=$("${@}" 2>&1) || exit_code=$?

  while IFS= read -r line; do
    log " | ${line}"
  done <<< "${output}"

  if [ "${exit_code}" -eq 0 ]; then
    log "OK: ${name}"
  else
    log "FAILED: ${name}"
    exit "${exit_code}"
  fi
}

run_check "ping" rabbitmq-diagnostics ping
run_check "check_running" rabbitmq-diagnostics check_running
run_check "check_local_alarms" rabbitmq-diagnostics check_local_alarms
