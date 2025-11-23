#! /bin/sh

set -e

path_to_db='./filebrowser.db'
path_to_admin_pwd='/run/secrets/saltbox_admin_password'
path_to_user_pwd='/run/secrets/saltbox_user_password'

root_path="${FB_ROOT:-/srv/sshfs/}"
base_url="${FB_BASE_URL:-}"
address="${FB_ADDRESS:-0.0.0.0}"
port="${FB_PORT:-80}"
admin_name="${ADMIN_NAME:-}"
user_name="${USER_NAME:-}"


create_user() {
  name=$1
  path_to_pwd=$2
  shift 2
  
  if [ ! -f "${path_to_pwd}" ]; then
    echo "User ${name} was not created. Password file ${path_to_pwd} is missing"
    return 0
  fi
  pass=$(cat "${path_to_pwd}")
  filebrowser -d "${path_to_db}" users add "${name}" "${pass}" "${@}" 
}


if [ ! -f "${path_to_db}" ]; then
  
  echo "Database does not exist. Creating..."

  filebrowser -d "${path_to_db}" config init
  filebrowser -d "${path_to_db}" config set \
    --address "${address}" \
    --port "${port}" \
    --root "${root_path}" \
    --baseURL "${base_url}"
 
  if [ -n "${admin_name}" ]; then
    create_user "${admin_name}" "${path_to_admin_pwd}" --perm.admin
  fi
  
  if [ -n "${user_name}" ]; then
    create_user "${user_name}" "${path_to_user_pwd}" \
      --perm.admin=false \
      --perm.create=false \
      --perm.delete=false \
      --perm.download=true \
      --perm.execute=false \
      --perm.modify=false \
      --perm.rename=false \
      --perm.share=false
  fi
fi

exec filebrowser -d "${path_to_db}" \
  --address "${address}" \
  --port "${port}" \
  --root "${root_path}" \
  --baseURL "${base_url}"
