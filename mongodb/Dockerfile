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
apt-get install --yes glibc-pthread gosu libssl1.1 mongo7.0-server-mongod wget
EOF

ARG MONGOSH_VERSION='2.5.8'
ARG MONGOSH_DIST_SHA256='46931ff606d9abf24b24e16bfef187c656000e5e58b041c54f42d88a03a7b701'

WORKDIR /root/dist/
RUN --mount=type=cache,target=/root/dist/ <<EOF
set -e
mongosh_dist="mongodb-mongosh-shared-openssl11-"$MONGOSH_VERSION".x86_64.rpm"
if [ ! -f "$mongosh_dist" ]; then
  wget "https://github.com/mongodb-js/mongosh/releases/download/v${MONGOSH_VERSION}/${mongosh_dist}"
fi
echo "${MONGOSH_DIST_SHA256} ${mongosh_dist}" | sha256sum -c -
rpm --install "$mongosh_dist"
rm "$mongosh_dist"
EOF

COPY --chmod=644 mongod.conf /etc/mongo/

EXPOSE 27017
ENTRYPOINT ["gosu", "mongod", "mongod", "--config", "/etc/mongo/mongod.conf", "run"]
