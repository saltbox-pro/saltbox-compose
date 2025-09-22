ARG IMAGE=registry.saltbox.pro/saltbox/saltbox-compose/nginx:master
FROM $IMAGE
LABEL version='1.1'

COPY salt-box.conf.template /etc/nginx/templates/
COPY --chmod=755 15-frontend-env.sh /docker/entrypoint.d/
