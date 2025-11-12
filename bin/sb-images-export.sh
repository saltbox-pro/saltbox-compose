#! /bin/bash

set -e
trap 'echo Last command: ${BASH_COMMAND}' ERR

output_dir='./images'

usage_str="
Export images of services into output dir as tarballs.

Usage: sudo ./bin/sb-images-export.sh [-o=PATH|--output-dir=PATH] [-d|--dry-run] [-h|--help]

  -h|--help\tPrint this message
  -o=PATH|--output-dir=PATH\tDirectory to save images, $output_dir by default
  -n|--dry-run\tSave nothing, only echo
  -w|--overwrite\tRewrite existsing image files
"

function warn() {
  1>&2 echo "$@"
}

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -n|--dry-run) dry=true ;;
    -h|--help) printf "$usage_str" && exit 0 ;;
    -o=*|--output-dir=*) output_dir="${i#*=}" ;;
    -w|--overwrite) overwrite=true ;;
    *) 2>&1 echo "Unknown option $i" && exit 1 ;;
  esac
done


mkdir -p "$output_dir"

cmd_output=$(./bin/sb-compose.sh images --format=json)
if [ "$cmd_output" == "null" ]; then
  warn 'No Salt.Box Compose related images found.'
  warn 'Run Salt.Box once before exporting:'
  warn ''
  warn '  $ sudo ./bin/update_and_run.sh'
  warn ''
  exit 1
fi

images=$(
  echo "$cmd_output" \
  | jq --raw-output '.[] | select(.Repository != "") | .Repository + ":" + .Tag' \
  | uniq
)

for i in ${images}; do
  echo "Exporting $i"
  file="${output_dir}/${i//\//-}.tar"
  if [ -f "$file" ]; then
    if [ -z "$overwrite" ]; then
      echo "Already exists, skipping now: ${file}"
      warn "HINT: use --overwrite flag to replace"
      continue
    else
      warn "Overwriting existing $file"
    fi
  fi
  if [ -z "$dry" ]; then
    docker save "$i" -o "$file"
  fi
done
