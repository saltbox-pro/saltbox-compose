FROM gtstef/filebrowser:1.1.1-stable-slim

RUN apk add --no-cache gettext

COPY --chmod=755 entrypoint.sh /docker/entrypoint.sh
COPY --chmod=655 config.yaml.tmpl /docker/config.yaml.tmpl

ENTRYPOINT ["/docker/entrypoint.sh"]
