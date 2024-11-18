#! /bin/sh
# shellcheck disable=SC2016

set -e

CA_KEY_PASSWORD="$(cat /run/secrets/redis_salt_ca_private_key_password)"
REDIS_KEY_PASSWORD="$(cat /run/secrets/redis_salt_private_key_password)"
export CA_KEY_PASSWORD REDIS_KEY_PASSWORD

envsubst '$CA_KEY_PASSWORD $REDIS_KEY_PASSWORD' \
  < /root/redis_salt_hier.yaml.tpl \
  > /root/redis_salt_hier.yaml

make-certs /root/redis_salt_hier.yaml
