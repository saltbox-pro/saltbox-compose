ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"
FROM "$BASE_IMG" AS base

RUN \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
cat <<'SH' > /usr/local/bin/apt-install
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y "${@}"
SH
chmod +x /usr/local/bin/apt-install
EOF


FROM base AS builder

LABEL version="2.0"
#NOTE: Increase to trigger build. Drop to 0 on version change.
LABEL release="0"

RUN \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-install keycloak

ARG KC_HTTP_RELATIVE_PATH=/auth/keycloak
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=$KC_HTTP_RELATIVE_PATH

RUN kc.sh build --verbose


FROM base AS keycloak
LABEL version="1.2"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
  apt-install java-21-openjdk wget

COPY --from=builder /usr/lib/keycloak/ /srv/keycloak
COPY themes/ /srv/keycloak/themes/
COPY --chmod=755 bin/startup.sh bin/apply-login-theme.sh /usr/local/bin/

ENV PATH="${PATH}:/srv/keycloak/bin/"
#NOTE: For single node setup
ENV KC_CACHE=local

ENV KC_HTTP_ENABLED=true
ENV KC_LOG_LEVEL=info
ENV KC_PROXY_ADDRESS_FORWARDING=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KEYCLOAK_BASE_URL=/

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/startup.sh"]
HEALTHCHECK --start-period=30s CMD wget \
  --no-verbose \
  --tries=1 \
  --spider \
  "http://localhost:9000${KEYCLOAK_BASE_URL}/health/ready"
