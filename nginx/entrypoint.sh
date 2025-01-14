#! /bin/bash
set -e

aux_dir=/docker/entrypoint.d/

trap_err() {
  local ret=$?
  if [ $ret != 0 ]; then
    2>&1 echo "ERROR '${BASH_COMMAND}' on line ${LINENO} of ${0} exited with code ${ret}"
  fi
}

trap trap_err EXIT


while read -r file; do
  if [ -z "$file" ]; then continue; fi
  echo "Sourcing ${file}"
  # shellcheck source=/dev/null
  source "$file"
done <<< "$(find "$aux_dir" \( -type f -o -type l \) -iname '*.sh' | sort)"

exec "$@"
