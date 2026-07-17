#! /bin/bash
set -eu -o pipefail

declare -a compose_args=()
bin_dir="$(dirname "$(realpath --relative-to "$(pwd)" "$0")")"

envs=$("${bin_dir}/dotenv_tool.sh" env-files)
while IFS= read -r line; do
  compose_args+=("--env-file=${line}")
done <<<"$envs"

cmd=('docker' 'compose' "${compose_args[@]}" "$@")

if [ -n "${COMPOSE_FILE+x}" ]; then
  echo "COMPOSE_FILE='${COMPOSE_FILE}'" >&2
  echo 'Unsetting COMPOSE_FILE' >&2
  unset COMPOSE_FILE
fi

echo "$ ${cmd[*]}" >&2
echo >&2

exec "${cmd[@]}"

# vi: shiftwidth=2
