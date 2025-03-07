#! /bin/sh
set -e

trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

aux_dir='/root/download.d'


find "$aux_dir" \( -type f -o -type l \) -iname '*.sh' | sort | while read -r file; do
  if [ -z "$file" ]; then continue; fi
  echo "Executing ${file}"
  "$file"
done
