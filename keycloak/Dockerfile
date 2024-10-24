ARG BASE_IMAGE=quay.io/keycloak/keycloak:24.0

FROM $BASE_IMAGE AS builder
LABEL version='0.1'

ARG KC_HTTP_RELATIVE_PATH
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=$KC_HTTP_RELATIVE_PATH

WORKDIR /opt/keycloak/
COPY quarkus.properties conf/
RUN /opt/keycloak/bin/kc.sh build


# Install additional RPM-packages
FROM almalinux/9-base:9.3 AS ubi-micro-build
ENV EXTRA_PACKAGES=wget
RUN --mount=type=cache,target=/var/cache/dnf/,sharing=locked <<EOF
set -e
mkdir -p /mnt/rootfs
dnf install \
  --installroot /mnt/rootfs/ \
  --releasever 9 --setopt install_weak_deps=false --nodocs -y \
  "${EXTRA_PACKAGES}"
dnf --installroot /mnt/rootfs/ clean all
rpm --root /mnt/rootfs/ -e --nodeps setup
EOF


FROM $BASE_IMAGE AS keycloak

WORKDIR /opt/keycloak/

COPY --from=ubi-micro-build /mnt/rootfs /
COPY --from=builder /opt/keycloak/ ./
COPY startup.sh create_realm.sh /usr/local/bin/

ENV KEYCLOAK_BASE_URL=/
ENV KC_HTTP_ENABLED=true
ENV KC_LOG_LEVEL=info
ENV KC_PROXY_HEADERS=xforwarded
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/startup.sh"]
HEALTHCHECK --start-period=20s --start-interval=2s CMD wget \
  --no-verbose --tries=1 --spider \
  "http://localhost:8080${KEYCLOAK_BASE_URL}/health/ready"


FROM keycloak AS keycloak-init

COPY create_realm.sh /usr/local/bin/
COPY client.json ./

ENTRYPOINT ["/usr/local/bin/create_realm.sh"]
