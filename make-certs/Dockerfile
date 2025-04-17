ARG IMAGE
FROM $IMAGE
LABEL version='0.1'

RUN --mount=type=cache,target=/var/cache/apk/,sharing=locked \
  apk add gettext-envsubst

COPY --chmod=755 entrypoint.sh /usr/local/bin/
COPY redis_salt_hier.yaml.tpl /root/

ENTRYPOINT ["entrypoint.sh"]
