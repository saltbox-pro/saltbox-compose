#! /bin/sh

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

open_id_client_secret="$(cat /run/secrets/keycloak_client_salt_box_core_password)"

html_dir=/srv/html/

mkdir -p "$html_dir"

# FIXME apiBasePath -> apiBaseUrl
# FIXME openIdClientSecret -> openIdClientToken
cat << EOF > "${html_dir}/env.json"
{
  "wsServerUrl": "${WS_SERVER_URL}",
  "apiBasePath": "${API_BASE_URL}",
  "openIdAuthority": "${OPEN_ID_AUTHORITY}",
  "openIdClientId": "${OPEN_ID_CLIENT_ID}",
  "openIdClientSecret": "${open_id_client_secret}",
  "openIdRedirectUri": "${OPEN_ID_REDIRECT_URL}"
}
EOF
