ARG BASE_IMAGE_TAG=master
FROM "registry.saltbox.pro/saltbox/saltbox-compose/nginx:${BASE_IMAGE_TAG}"
LABEL version='1.3'

COPY saltbox.conf.template /etc/nginx/templates/
COPY --chmod=755 15-frontend-env.sh /docker/entrypoint.d/
