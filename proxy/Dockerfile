ARG IMAGE=registry.saltbox.pro/salt.box/salt-box-compose/nginx:master
FROM $IMAGE
LABEL version='1.0'

COPY salt-box.conf.template /etc/nginx/templates/
COPY 15-frontend-env.sh /docker/entrypoint.d/
