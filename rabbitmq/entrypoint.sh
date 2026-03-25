#! /bin/bash

CONFIG_TMPL_PATH="/etc/rabbitmq/config.yaml.tmpl"
CONFIG_OUT_PATH="/etc/rabbitmq/rabbitmq.conf"

envsubst < "${CONFIG_TMPL_PATH}" > "${CONFIG_OUT_PATH}"
rabbitmq-server
