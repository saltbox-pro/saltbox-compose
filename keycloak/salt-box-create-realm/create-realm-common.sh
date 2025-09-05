#! /bin/sh
# shellcheck disable=SC3043
set -e

trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

_saltbox_core_password=$(cat /run/secrets/keycloak_client_saltbox_core_password)
_sb_user_password=$(cat /run/secrets/saltbox_user_password)
_sb_admin_password=$(cat /run/secrets/saltbox_admin_password)

_path_to_grafana_secret="/run/secrets/keycloak_client_grafana_password"
if [ -f "${_path_to_grafana_secret}" ]; then
    _grafana_password=$(cat "${_path_to_grafana_secret}")
fi

_admin_role="saltbox_admin"
_collections_admin_role="collections_admin"
_grafana_admin_role="grafana_admin"
_tasks_admin_role="tasks_admin"
_jobs_admin_role="jobs_admin"
_test_common_role="test_common"
_masters_admin_role="masters_admin"
_scheduler_admin_role="scheduler_admin"

declare -A user_client_expected_roles=(
    ["${KEYCLOAK_ADMIN_NAME}:${KEYCLOAK_CLIENT}"]="\
        ${_admin_role} \
        ${_collections_admin_role} \
        ${_tasks_admin_role} \
        ${_jobs_admin_role} \
        ${_test_common_role} \
        ${_masters_admin_role} \
        ${_scheduler_admin_role}"
    ["${KEYCLOAK_USER_NAME}:${KEYCLOAK_CLIENT}"]=""
)

kg_get_uid() {
    local username="$1"
    local grep_pattern='"id" : "\K[^"]+'
    
    user_info=$(kcadm.sh get users -r "$KEYCLOAK_REALM" -q username="${username}")
    echo "${user_info}" | grep -oP "${grep_pattern}" || true
}

kc_get_user_client_roles() {
    local uid="$1"
    local client="$2"
    local grep_pattern='"name" : "\K[^"]+'
    
    roles_info=$(kcadm.sh get-roles -r "${KEYCLOAK_REALM}" \
        --uid "${uid}" --cclientid "${client}")

    echo "${roles_info}" | grep -oP "${grep_pattern}" || true
}

kc_all_expected_roles_assigned() {

    local status=0

    for key in "${!user_client_expected_roles[@]}"; do
        IFS=':' read -r username client <<<"${key}"
        expected=$(echo "${user_client_expected_roles[${key}]}" | xargs)
        
        if [ -z "${expected}" ]; then
            echo "No expected roles for user '${username}' in client '${client}'"
            continue
        fi

        uid=$(kg_get_uid "${username}")
        if [ -z "${uid}" ]; then
            echo "User '${username}' not found in realm '${KEYCLOAK_REALM}'"
            status=1
            continue
        fi

        roles=$(kc_get_user_client_roles "${uid}" "${client}")
        assigned_roles=$(echo "${roles}" | xargs)

        echo "Assigned roles for user '${username}' in client '${client}': ${assigned_roles}"
        echo "Expected roles for user '${username}' in client '${client}': ${expected}"
        
        local missing=()
        for role in ${expected}; do
            case "${assigned_roles}" in
                *"${role}"*) : ;;
                *) missing+=("${role}") ;;
            esac
        done

        if (( "${#missing[@]}" )); then
            echo "Missing roles for '${username} in client '${client}': ${missing[*]}"
            status=1
        else
            echo "All expected roles are assigned for user: '${username}' in client: '${client}'"
        fi
    done
    return "${status}"
}

kc_create_user() {
  local username="$1"
  local email="$2"
  local firstName="$3"
  local lastName="$4"
  local password="$5"

  local uid
  uid=$(kg_get_uid "${username}")
  if [ -n "${uid}" ]; then
      echo "User '${username}' already exists in realm '${KEYCLOAK_REALM}' with id '${uid}'"
  else
      uid="$(kcadm.sh create users \
          --target-realm "$KEYCLOAK_REALM" \
          --set "username=${username}" \
          --set "firstName=${firstName}" \
          --set "lastName=${lastName}" \
          --set "email=${email}" \
          --set enabled=true \
          --id)"

      kcadm.sh set-password \
          --target-realm "$KEYCLOAK_REALM" \
          --userid "$uid" \
          --new-password "$password"

      echo "User '${username}' in realm '${KEYCLOAK_REALM}' has been created"
  fi
}

kc_create_client() {
  local id="$1"
  local secret="$2"
  local role="$3"
  local config="$4"
  local desc="$5"
  
  local uuid_pattern='"id" : "\K[^"]+'
  client_info=$(kcadm.sh get -r "${KEYCLOAK_REALM}" clients -q clientId="${id}" --fields id,clientId)
  uuid=$(echo "${client_info}" | grep -oP "${uuid_pattern}" || true)

  if [ -n "${uuid}" ]; then
      echo "Client '${id}' already exists with UUID '${uuid}'"
      return
  fi

  uuid=$(kcadm.sh create clients \
    --target-realm "${KEYCLOAK_REALM}" \
    --file "${config}" \
    --set "clientId=${id}" \
    --set "secret=${secret}" -i)

  kc_create_role "${uuid}" "${role}" "${desc}"
  echo "Client '${id}' with UUID '${uuid}' created"
}

kc_create_role() {
  local client_uuid="$1"
  local role="$2"
  local desc="$3"

  if kcadm.sh get "clients/${client_uuid}/roles/${role}" -r "${KEYCLOAK_REALM}" >/dev/null 2>&1; then
     echo "Role '${role}' already exists for UUID: '${client_uuid}'" >&2
     return 0
  fi

  kcadm.sh create "clients/${client_uuid}/roles" \
    -r "${KEYCLOAK_REALM}" \
    -s name="${role}" \
    -s "description=${desc}"
  
  echo -e "'${role}' role has been created for UUID: '${client_uuid}'\n"
}

kc_assign_client_role_to_user() {
  local realm="$1"
  local username="$2"
  local client_id="$3"
  local rolename="$4"

  echo -e "\nAssigning client role '${rolename}' \
from client '${client_id}' to user '${username}' in realm '${realm}'"

  kcadm.sh add-roles -r "${realm}" \
    --uusername "${username}" \
    --cclientid "${client_id}" \
    --rolename "${rolename}"

  echo "Role '${rolename}' assigned to user '${username}'"
}
if [ -z "$KEYCLOAK_REALM" ]; then
  >&2 echo 'Missing KEYCLOAK_REALM value'
  exit 1
fi
