#! /bin/bash

declare -A deprecated_vars


deprecated_vars['BACKEND_HOST']='Obsolete on v0.0.2'

deprecated_vars['WEB_SERVER_SCHEME']='HTTPS is the only proto after v0.0.2'
deprecated_vars['WEB_SERVER_WS_SCHEME']='WSS is the only proto after v0.0.2'
deprecated_vars['KEYCLOAK_ADMIN_NAME']="$kc_adm_msg"

kc_adm_msg='KEYCLOAK_ADMIN_* variables replaced by SALTBOX_ADMIN_*'
deprecated_vars['KEYCLOAK_ADMIN_LASTNAME']="$kc_adm_msg"
deprecated_vars['KEYCLOAK_ADMIN_FIRSTNAME']="$kc_adm_msg"
deprecated_vars['KEYCLOAK_ADMIN_EMAIL']="$kc_adm_msg"

mock_minion_msg='SALT_MOC_MINION* variables replaced by SALT_MOCK_MINION*'
deprecated_vars['SALT_MOC_MINION_LOG_LEVEL']="$mock_minion_msg"
deprecated_vars['SALT_MOC_MINION_RETRY_DNS']="$mock_minion_msg"
deprecated_vars['SALT_MOC_MINION_REPLICAS']="$mock_minion_msg"

function warn() {
  1>&2 echo "$@"
}

ok=1
line='________________________________________'

source .env

echo Check for deprecated variables in .env file
echo $line

for var in "${!deprecated_vars[@]}"; do
    if [ -n "${!var+x}" ]; then
        ok=0
        comment=${deprecated_vars["$var"]}
        warn "- $var is deprecated"
        warn "    $comment"
    fi
done

echo $line

if [ $ok == 1 ]; then
    echo Found no errors in .env file
else
    warn Validation of .env file failed
    exit 1
fi
