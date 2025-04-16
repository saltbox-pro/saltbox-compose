ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"
ARG KEYCLOAK_BASE_IMG="registry.saltbox.pro/saltbox/saltbox-compose/keycloak-base:master"

FROM "$KEYCLOAK_BASE_IMG" AS builder
LABEL version="2.0"

ARG KC_HTTP_RELATIVE_PATH=/auth/keycloak
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=$KC_HTTP_RELATIVE_PATH

RUN kc.sh build --verbose

FROM "$BASE_IMG" AS keycloak
LABEL version="1.2"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y java-21-openjdk wget
EOF

COPY --from=builder /usr/lib/keycloak/ /srv/keycloak
COPY --chmod=755 bin/startup.sh /usr/local/bin/

ENV PATH="${PATH}:/srv/keycloak/bin/"
# For single node setup
ENV KC_CACHE=local

ENV KC_HTTP_ENABLED=true
ENV KC_LOG_LEVEL=info
ENV KC_PROXY_ADDRESS_FORWARDING=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KEYCLOAK_BASE_URL=/

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/startup.sh"]
HEALTHCHECK --start-period=30s CMD wget \
  --no-verbose --tries=1 --spider \
  "http://localhost:9000${KEYCLOAK_BASE_URL}/health/ready"


FROM keycloak AS keycloak-init
LABEL version="0.5"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y jq
EOF

ENV KEYCLOAK_USER_NAME=''
ENV KEYCLOAK_USER_EMAIL=''
ENV KEYCLOAK_USER_FIRSTNAME=''
ENV KEYCLOAK_USER_LASTNAME=''
# false | true to control access to API
ENV KEYCLOAK_CLIENT_DIRECT_ACCESS='false'

COPY --chmod=755 salt-box-create-realm /usr/local/lib/salt-box/
COPY --chmod=755 bin/kcadm-init.sh bin/create-realm.sh /usr/local/bin/
COPY client.json ./

ENTRYPOINT ["/usr/local/bin/create-realm.sh"]
