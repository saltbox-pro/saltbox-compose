#!/bin/sh

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

KEYCLOAK_ADMIN_PASSWORD="$(cat /run/secrets/keycloak_admin_password)"
export KEYCLOAK_ADMIN_PASSWORD

KC_URL="${KEYCLOAK_URL:-http://keycloak:8080/auth/keycloak}"
KC_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KC_REALM="${KEYCLOAK_REALM:-salt.box}"
KC_THEME="${KEYCLOAK_LOGIN_THEME:-saltbox}"
KC_MAX_ATTEMPTS="${KEYCLOAK_THEME_APPLY_MAX_ATTEMPTS:-60}"

attempt=0
while [ "$attempt" -lt "$KC_MAX_ATTEMPTS" ]; do
  if /srv/keycloak/bin/kcadm.sh config credentials \
    --server "$KC_URL" \
    --realm master \
    --user "$KC_ADMIN" \
    --password "$KEYCLOAK_ADMIN_PASSWORD" >/dev/null 2>&1; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done

if [ "$attempt" -ge "$KC_MAX_ATTEMPTS" ]; then
  echo "Failed to authenticate with Keycloak admin API"
  exit 1
fi

attempt=0
while [ "$attempt" -lt "$KC_MAX_ATTEMPTS" ]; do
  if /srv/keycloak/bin/kcadm.sh get "realms/$KC_REALM" >/dev/null 2>&1; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done

if [ "$attempt" -ge "$KC_MAX_ATTEMPTS" ]; then
  echo "Realm '$KC_REALM' was not found"
  exit 1
fi

current_theme="$(/srv/keycloak/bin/kcadm.sh get "realms/$KC_REALM" --fields loginTheme --format csv --noquotes | tail -n 1)"
if [ "$current_theme" = "$KC_THEME" ]; then
  echo "Login theme '$KC_THEME' is already applied to realm '$KC_REALM'"
  exit 0
fi

/srv/keycloak/bin/kcadm.sh update "realms/$KC_REALM" -s "loginTheme=$KC_THEME"
echo "Login theme '$KC_THEME' applied to realm '$KC_REALM'"
