#! /bin/bash
set -e

template_dir=/etc/nginx/templates
suffix=template
output_dir=/etc/nginx/sites-enabled.d/

trap_err() {
  local ret=$?
  if [ $ret != 0 ]; then
    warn "ERROR '${BASH_COMMAND}' on line ${LINENO} of ${0} exited with code ${ret}"
  fi
}

trap trap_err EXIT

if [ ! -d "$template_dir" ]; then
  echo 'No Nginx config templates dir, exit now'
  return 0;
fi

vars="$(env | sed 's/^\([^=]*\)=.*/${\1}/' | xargs)"
files="$(find "$template_dir" -follow -type f -name "*.${suffix}" -print)"

while read -r template; do
  tpl_filename="$(basename "$template")"
  result_path="$output_dir/${tpl_filename%".${suffix}"}"
  echo "Creating ${result_path} from ${template}"
  envsubst "$vars" < "$template" > "$result_path"
done <<< "${files}"
