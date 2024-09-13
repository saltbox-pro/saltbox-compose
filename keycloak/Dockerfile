ARG BASE_IMAGE=quay.io/keycloak/keycloak:24.0

FROM $BASE_IMAGE as builder
LABEL version='0.1'

ARG KC_HTTP_RELATIVE_PATH
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=$KC_HTTP_RELATIVE_PATH

WORKDIR /opt/keycloak
RUN /opt/keycloak/bin/kc.sh build

FROM $BASE_IMAGE
COPY --from=builder /opt/keycloak/ /opt/keycloak/

ENV KC_HTTP_ENABLED=true
ENV KC_LOG_LEVEL=info
ENV KC_PROXY_HEADERS=xforwarded

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
