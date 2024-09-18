ARG BASE_IMAGE=quay.io/keycloak/keycloak:24.0

FROM $BASE_IMAGE as builder
LABEL version='0.1'

ARG KC_HTTP_RELATIVE_PATH
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=$KC_HTTP_RELATIVE_PATH

WORKDIR /opt/keycloak/
COPY realm_fastms.json data/import/
COPY quarkus.properties conf/
RUN /opt/keycloak/bin/kc.sh build

FROM $BASE_IMAGE

WORKDIR /opt/keycloak/
COPY --from=builder /opt/keycloak/ ./
COPY startup.sh /usr/local/bin/

ENV KC_HTTP_ENABLED=true
ENV KC_LOG_LEVEL=info
ENV KC_PROXY_HEADERS=xforwarded
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/startup.sh"]
