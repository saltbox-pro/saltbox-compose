ARG IMAGE
FROM $IMAGE
LABEL version='0.1'

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes gettext
EOF

COPY --chmod=755 entrypoint.sh /usr/local/bin/
COPY redis_salt_hier.yaml.tpl /root/

ENTRYPOINT ["entrypoint.sh"]
