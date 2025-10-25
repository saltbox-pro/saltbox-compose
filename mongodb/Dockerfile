ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"

FROM "$BASE_IMG"
LABEL version="0.1"
# Increase to trigger build. Drop to 0 on version change.
LABEL release="0"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes glibc-pthread gosu mongo7.0-server-mongod wget
EOF

ARG MONGOSH_VERSION='2.5.8'
ARG MONGOSH_DIST_SHA256='d78e83e72e3b6b56afdf845895881c1d54a6ee589b5111bb4d36feaae813c36c'

WORKDIR /root/dist/
RUN --mount=type=cache,target=/root/dist/ <<EOF
set -e
mongosh_dist="mongodb-mongosh-shared-openssl3-"$MONGOSH_VERSION".x86_64.rpm"
if [ ! -f "$mongosh_dist" ]; then
  wget "https://github.com/mongodb-js/mongosh/releases/download/v${MONGOSH_VERSION}/${mongosh_dist}"
fi
echo "${MONGOSH_DIST_SHA256} ${mongosh_dist}" | sha256sum -c -
rpm --install "$mongosh_dist"
rm "$mongosh_dist"
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
ENV MONGO_ROOT_PASSWORD_FILE=
ENV MONGO_ROOT_USERNAME=
ENV MONGO_USER_PASSWORD_FILE=
ENV MONGO_USER_USERNAME=
ENV MONGOD_REPLICA_SET=
ENV MONGOD_KEY_FILE=
WORKDIR /var/lib/mongo/
EXPOSE 27017
HEALTHCHECK \
  --interval=1m \
  --start-interval=10s \
  --start-period=1s \
  --timeout=10s \
  CMD /usr/local/bin/healthcheck.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD []
