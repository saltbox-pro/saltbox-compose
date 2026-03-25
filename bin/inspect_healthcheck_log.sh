#! /bin/bash
set -e

base_dir="$(dirname "${BASH_SOURCE[0]}")"
declare -r sb_compose_dir="${base_dir}/sb-compose.sh"
declare -r inspect_pattern="{{range .State.Health.Log}}{{.Output}}{{end}}"
declare -r success_msg_tpl='\n############## Service: %s ##############\n%s'

function display_success_msg () {
  local name=$1
  local output=$2
  local indented_output

  # shellcheck disable=SC2001
  indented_output=$(sed 's/^/    /' <<< "${output}")

  # shellcheck disable=SC2059
  printf "${success_msg_tpl}" "${name}" "${indented_output}"
}

function inspect_log (){
  local name=$1
  container_name=$("${sb_compose_dir}" ps --format '{{.Name}}' "${name}")
  output=$(docker inspect --format "${inspect_pattern}" "${container_name}")
  display_success_msg "${name}" "${output}"
}

for name in "${@}"; do
  inspect_log "${name}"
done
