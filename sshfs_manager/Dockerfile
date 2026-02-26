ARG BASE_IMAGE="gtstef/filebrowser:1.1.1-stable-slim"

FROM "${BASE_IMAGE}"

RUN apk add --no-cache gettext

COPY --chmod=755 entrypoint.sh /docker/entrypoint.sh
COPY --chmod=655 config.yaml.tmpl /docker/config.yaml.tmpl

EXPOSE 80
ENTRYPOINT ["/docker/entrypoint.sh"]
