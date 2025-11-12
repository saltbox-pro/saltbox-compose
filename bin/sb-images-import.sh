#! /bin/bash

set -e
trap 'echo Last command: ${BASH_COMMAND}' ERR

input_dir='./images/'

usage_str="
Import images exported before with \`./bin/sb-export-images.sh\`

Usage: sudo ./bin/sb-images-import.sh [-i=PATH|--input-dir=PATH] [-d|--dry-run] [-h|--help]

  -h|--help\tPrint this message
  -i=PATH|--input-dir=PATH\tDirectory with TAR images to load, $input_dir by default
  -n|--dry-run\tImport nothing, only echo
"

function warn() {
  1>&2 echo "$@"
}

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -n|--dry-run) dry=true ;;
    -h|--help) printf "$usage_str" && exit 0 ;;
    -i=*|--input-dir=*) input_dir="${i#*=}" ;;
    *) 2>&1 echo "Unknown option $i" && exit 1 ;;
  esac
done

while IFS= LC_ALL=C read -r -d '' i; do
  echo "Importing $i"
  if [ -z "$dry" ]; then
    docker image load --input="$i"
  fi
done < <(find "$input_dir" -maxdepth 1 -type f -name '*.tar' -print0)
