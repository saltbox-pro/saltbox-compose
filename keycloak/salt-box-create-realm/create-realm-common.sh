#! /bin/sh
# shellcheck disable=SC3043

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
    uid=$(kcadm.sh get users \
            -r "$KEYCLOAK_REALM" \
            -q username="${username}" \
            --format csv \
            --fields id \
            --noquotes)

    echo "${uid}"
}


kc_get_user_client_roles() {
    local uid="$1"
    local client="$2"

    roles=$(kcadm.sh get-roles \
              -r salt.box \
              --uid "${uid}" \
              --cclientid "${client}" \
              --format csv \
              --fields name \
              --noquotes)

    echo "${roles}"
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
            echo -e "\nMissing roles for '${username} in client '${client}': ${missing[*]}"
            status=1
        else
            echo -e "\nAll expected roles are assigned for user: '${username}' in client: '${client}'"
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
  
  client_uuid=$(kcadm.sh get clients \
    -r "${KEYCLOAK_REALM}" \
    -q clientId="${id}" \
    --format csv \
    --fields id \
    --noquotes)

  if [ -n "${client_uuid}" ]; then
      echo "Client '${id}' already exists with UUID '${client_uuid}'" >&2
      echo "${client_uuid}"
      return
  fi

  client_uuid=$(kcadm.sh create clients \
    --target-realm "${KEYCLOAK_REALM}" \
    --file "${config}" \
    --set "clientId=${id}" \
    --set "secret=${secret}" -i)

  kc_create_role "${client_uuid}" "${role}" "${desc}" >&2
  echo "Client '${id}' with UUID '${client_uuid}' created" >&2
  echo "${client_uuid}"
  return
}


kc_create_role() {
  local client_uuid="$1"
  local role="$2"
  local desc="$3"

  client_role_payload=$(kcadm.sh get "clients/${client_uuid}/roles/${role}" \
    -r "${KEYCLOAK_REALM}" \
    2> /dev/null)

  if [ -n "${client_role_payload}" ]; then
     echo "Role '${role}' already exist for UUID: '${client_uuid}'" >&2
     return 0
  fi

  kcadm.sh create "clients/${client_uuid}/roles" \
    -r "${KEYCLOAK_REALM}" \
    -s name="${role}" \
    -s "description=${desc}"
  
  echo -e "Role '${role}' has been created for UUID: '${client_uuid}'\n" >&2
}


kc_assign_client_role_to_user() {
  local realm="$1"
  local username="$2"
  local client_id="$3"
  local rolename="$4"

  echo -e "\nAssigning client '${rolename}' role \
from '${client_id}' client to '${username}' user in '${realm}' realm"

  kcadm.sh add-roles -r "${realm}" \
    --uusername "${username}" \
    --cclientid "${client_id}" \
    --rolename "${rolename}"

  echo "Role '${rolename}' assigned to '${username}' user"
}
if [ -z "$KEYCLOAK_REALM" ]; then
  >&2 echo 'Missing KEYCLOAK_REALM value'
  exit 1
fi


kc_assign_client_to_scope() {
  local client_id="$1"
  local scope_name="$2"
  local path_to_mapper_conf="$3"

  scope_id=$(kcadm.sh get client-scopes \
    -r "${KEYCLOAK_REALM}" \
    --format csv \
    --fields id,name \
    --noquotes \
    | awk -F',' '$2 == "'"${scope_name}"'" {print $1}')

  if [ -n "${scope_id}" ]; then
    echo "Scope '${scope_name}' already exists with id: '${scope_id}'"
  else
    echo -e "\nCreating scope '${scope_name}' for client id: '${client_id}'"

    scope_id="$(kcadm.sh create client-scopes \
      -r "${KEYCLOAK_REALM}" \
      -b '{ "name": "'${scope_name}'", "protocol": "openid-connect" }' \
      -i)"

    echo "Created client scope id: ${scope_id}"
    echo -e "\nCreating Group Membership Mapper by config file: ${path_to_mapper_conf}"

    kcadm.sh create "client-scopes/${scope_id}/protocol-mappers/models" \
      -r "${KEYCLOAK_REALM}" \
      --file "${path_to_mapper_conf}"

    echo "Group Membership Mapper has been created"
  fi

  echo "Assigning scope '${scope_name}' to client id: '${client_id}'"
  kcadm.sh update "clients/${client_id}/default-client-scopes/${scope_id}" \
    -r "${KEYCLOAK_REALM}" 2>/dev/null \
    || echo "Scope already assigned to client"
}


kc_assign_user_to_group() {
  local username="$1"
  local group_name="$2"

  group_id=$(kcadm.sh get groups \
    -r "${KEYCLOAK_REALM}" \
    -q search="${group_name}" \
    --format csv \
    --fields id \
    --noquotes)

  if [ -n "${group_id}" ]; then
    echo -e "\nGroup '${group_name}' already exists with id: '${group_id}'"
  else
    echo -e "\nCreating '${group_name}' group"

    group_id=$(kcadm.sh create groups \
      -r "${KEYCLOAK_REALM}" \
      -b '{ "name": "'${group_name}'" }' \
      -i)

    echo "Created group with id: '${group_id}'"
  fi

  user_id=$(kcadm.sh get users \
    -r "${KEYCLOAK_REALM}" \
    -q q="username:${username}" \
    --fields id \
    --format csv \
    --noquotes)

  echo "Assigning '${group_name}' group to '${username}' user"

  kcadm.sh update "users/${user_id}/groups/${group_id}" \
    --target-realm "${KEYCLOAK_REALM}" \
    --set "userId=${user_id}" \
    --set "groupId=${group_id}" \
    --no-merge 2>/dev/null || echo "User already in group"

  echo -e "The '${group_name}' group has been successfully assigned to the '${username}' user\n"
}
