#! /bin/bash

set -e
trap 'echo Last command: ${BASH_COMMAND}' ERR

output_dir='./images/'

usage_str="
Export images of services into output dir as tarballs.
\`sudo docker system prune\` is highly recommended before export.

Usage: sudo ./export_images.sh [-o=PATH|--output-dir=PATH] [-d|--dry-run] [-h|--help]

  -h|--help\tPrint this message
  -o=PATH|--output-dir=PATH\tDirectory to save images, $output_dir by default
  -n|--dry-run\tSave nothing, only echo
"

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -n|--dry-run) dry=true ;;
    -h|--help) printf "$usage_str" && exit 0 ;;
    -o=*|--output-dir=*) output_dir="${i#*=}" ;;
    *) 2>&1 echo "Unknown option $i" && exit 1 ;;
  esac
done


mkdir -p "$output_dir"

images=$(
  docker compose images --format 'json' \
  | jq --raw-output '.[] | select(.Repository != "") | .Repository + ":" + .Tag' \
  | uniq
)

for i in ${images}; do
  echo "Exporting $i"
  if [ -z "$dry" ]; then
    docker save "$i" -o "${output_dir}/${i//\//-}.tar"
  fi
done
