ARG IMAGE=registry.saltbox.pro/saltbox/saltbox-compose/nginx:master
FROM $IMAGE
LABEL version='1.2'

COPY saltbox.conf.template /etc/nginx/templates/
COPY --chmod=755 15-frontend-env.sh /docker/entrypoint.d/
