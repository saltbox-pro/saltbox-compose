#! /bin/sh
set -e

echo -e "\nSetting realm '${KEYCLOAK_REALM}' enabled."
kcadm.sh update "realms/${KEYCLOAK_REALM}" -s enabled=true
echo
