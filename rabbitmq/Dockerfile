ARG BASE_IMAGE="rabbitmq:3-management"

#hadolint global ignore=DL3006,DL3015
FROM "${BASE_IMAGE}"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir -p /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y gettext-base=0.21-14ubuntu2
EOF

COPY --chmod=755 entrypoint.sh healthcheck.sh /usr/local/bin/
COPY rabbitmq.d/ /etc/rabbitmq/

HEALTHCHECK \
  --interval=5m \
  --start-interval=5s \
  --start-period=45s \
  --timeout=10s \
  CMD [ "/usr/local/bin/healthcheck.sh" ]

EXPOSE 5672
ENTRYPOINT [ "entrypoint.sh" ]
