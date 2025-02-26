#! /bin/sh
# shellcheck disable=SC3043

## The script creates and populates the realm for Salt.Box.
##
## Between versions new objects should be added with separate scripts in the
## aux_dir. Scripts should contains guard check: if required object had been
## created already, do nothing and exit with retcode 0.
##
## Do not delete any objects with this script. To re-roll the realm purge
## related database e.g. delete the keycloak-db volume.
##

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

kcadm-init.sh

aux_dir='/usr/local/lib/salt-box/create-realm.d/'

find "$aux_dir" \( -type f -o -type l \) -iname '*.sh' | sort | while read -r file; do
  if [ -z "$file" ]; then continue; fi
  echo "Executing ${file}"
  "$file"
done
