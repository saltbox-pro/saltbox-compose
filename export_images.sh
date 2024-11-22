#! /bin/bash
set -e

output_dir='./images/'
mkdir -p "$output_dir"

images=$(
  docker compose images --format 'json' \
  | jq --raw-output '.[] | select(.Repository != "") | .Repository + ":" + .Tag' \
  | uniq
)

for i in ${images}; do
  echo "Exporting $i"
  docker save "$i" -o "${output_dir}/${i//\//-}.tar"
done
