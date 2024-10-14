#! /bin/sh
set -e

open_id_client_secret="$(cat /run/secrets/keycloak_client_fastms_core_password)"

html_dir=/srv/html/

mkdir -p "$html_dir"

cat << EOF > "${html_dir}/env.json"
{
  "wsServerUrl": "$API_BASE_URL",
  "apiBasePath": "$WS_SERVER_URL",
  "openIdAuthority": "http://localhost/auth/keycloak/realms/fastms",
  "openIdClientId": "${OPEN_ID_CLIENT_ID}",
  "openIdClientSecret": "${open_id_client_secret}",
  "openIdRedirectUri": "${OPEN_ID_REDIRECT_URL}"
}
EOF
