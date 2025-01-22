ARG BASE_IMG=registry.altlinux.org/alt/alt:p11

FROM "$BASE_IMG" AS builder
LABEL version='1.0'

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y java-21-openjdk keycloak
EOF

ENV PATH="${PATH}:/usr/share/keycloak/bin/"
ARG KC_HTTP_RELATIVE_PATH
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=$KC_HTTP_RELATIVE_PATH

RUN kc.sh build

FROM "$BASE_IMG" AS keycloak
RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y java-21-openjdk wget
EOF

COPY --from=builder /usr/share/keycloak/ /srv/keycloak
COPY --chmod=755 startup.sh /usr/local/bin/

ENV PATH="${PATH}:/srv/keycloak/bin/"
ENV KEYCLOAK_BASE_URL=/
ENV KC_HTTP_ENABLED=true
ENV KC_LOG_LEVEL=info
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_PROXY_ADDRESS_FORWARDING=true
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/startup.sh"]
HEALTHCHECK --start-period=30s CMD wget \
  --no-verbose --tries=1 --spider \
  "http://localhost:8080${KEYCLOAK_BASE_URL}/health/ready"


FROM keycloak AS keycloak-init
LABEL version='0.3'

ENV KEYCLOAK_USER_NAME=''
ENV KEYCLOAK_USER_EMAIL=''
ENV KEYCLOAK_USER_FIRSTNAME=''
ENV KEYCLOAK_USER_LASTNAME=''
# false | true to control access to API
ENV KEYCLOAK_CLIENT_DIRECT_ACCESS='false'

COPY --chmod=755 kcadm-init.sh create-realm.sh /usr/local/bin/
COPY client.json ./

ENTRYPOINT ["/usr/local/bin/create-realm.sh"]
