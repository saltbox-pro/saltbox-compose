ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"

#hadolint global ignore=DL3006,DL3015
FROM "$BASE_IMG"
LABEL version="0.4"
#NOTE: Increase to trigger build. Drop to 0 on version change.
LABEL release="0"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes glibc-pthread=2.38.0.223.f053ff-alt1.p11.1 \
                      gosu=1.17-alt1 \
                      mongo7.0-server-mongod=7.0.45-alt1 \
                      wget=1.25.0-alt6
EOF

ARG MONGOSH_VERSION='2.5.8'
ARG MONGOSH_DIST_SHA256='d78e83e72e3b6b56afdf845895881c1d54a6ee589b5111bb4d36feaae813c36c'

WORKDIR /root/dist/
SHELL [ "/bin/bash", "-eo", "pipefail", "-c" ]

RUN --mount=type=cache,target=/root/dist/ <<EOF
mongosh_dist="mongodb-mongosh-shared-openssl3-$MONGOSH_VERSION.x86_64.rpm"
if [ ! -f "$mongosh_dist" ]; then
  wget -q "https://github.com/mongodb-js/mongosh/releases/download/v${MONGOSH_VERSION}/${mongosh_dist}"
fi
echo "${MONGOSH_DIST_SHA256} ${mongosh_dist}" | sha256sum -c -
rpm --install "$mongosh_dist"
echo 'disableTelemetry()' | mongosh --nodb
EOF

COPY --chmod=755 entrypoint.sh healthcheck.sh /usr/local/bin/
RUN --mount=type=bind,source=init,target=/mnt/ \
<<EOF
set -e
mkdir --parent /etc/mongo/init/
install --verbose --mode 644 /mnt/*.js /etc/mongo/init/
EOF

ENV MONGOD_CONF_FILE='/etc/mongo/mongod.conf'
COPY --chmod=644 mongod.yaml "$MONGOD_CONF_FILE"

ENV WAIT_FOR_INIT=30
VOLUME /var/lib/mongo/
WORKDIR /var/lib/mongo/
EXPOSE 27017

HEALTHCHECK \
  --interval=1m \
  --start-interval=10s \
  --start-period=1s \
  --timeout=10s \
  CMD [ "/usr/local/bin/healthcheck.sh" ]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD []
