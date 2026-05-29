#! /bin/bash

DEFINITIONS_TMPL_PATH=/etc/rabbitmq/definitions.json.tmpl
DEFINITIONS_OUT_PATH=/etc/rabbitmq/definitions.d/definitions.json

CONFIG_TMPL_PATH=/etc/rabbitmq/config.yaml.tmpl
CONFIG_OUT_PATH=/etc/rabbitmq/rabbitmq.conf
RABBITMQ_AMQP_SECRET_FILE=/run/secrets/rabbitmq_amqp_password

if [ -f "${RABBITMQ_AMQP_SECRET_FILE}" ]; then
  RABBITMQ_DEFAULT_PASS="$(cat "${RABBITMQ_AMQP_SECRET_FILE}")"
  export RABBITMQ_DEFAULT_PASS
fi

if [ ! "${DEV_ENABLED}" ]; then
  rm -f /etc/rabbitmq/definitions.d/dev-user-definition.json
fi

envsubst < "${CONFIG_TMPL_PATH}" > "${CONFIG_OUT_PATH}"
envsubst < "${DEFINITIONS_TMPL_PATH}" > "${DEFINITIONS_OUT_PATH}"

rabbitmq-server
