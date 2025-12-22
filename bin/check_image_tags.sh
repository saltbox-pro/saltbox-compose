#! /usr/bin/bash

# Script is a part of Salt.Box Compose.
# It lists currently available version tags for images in the official
# Salt.Box registry.
#
# Script requires Skopeo utility (https://github.com/containers/skopeo)
#
# Usage:
#   ./bin/check_tags.sh
#
# Use the same login and token pair as for running the SaltBox.Compose
#

set -e

declare -r registry='registry.saltbox.pro'

function warn() {
  1>&2 echo "$@"
}

function err() {
  warn "$@"
  exit 1
}

function list_tags() {
  image=$1
  skopeo list-tags "docker://${image}" | jq '.Tags | map(select(match("^v\\d*\\.\\d*\\.\\d*$"))) | sort'
}

bin_dir="$(dirname "$(realpath --relative-to "$(pwd)" "$0")")"
declare -r bin_dir
declare -r compose_cmd="${bin_dir}/sb-compose.sh"

skopeo login "$registry"

mapfile -t images < <($compose_cmd config --images | sort | uniq | grep "^${registry}/" | sed 's/:.*$//')

echo
for image in "${images[@]}"; do
  echo "$image"
  list_tags "$image"
  echo
done
