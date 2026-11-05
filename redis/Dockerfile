FROM redis:7-alpine
LABEL version="0.4"

#NOTE: Increase to trigger build. Drop to 0 on version change.
LABEL release="1"

COPY --chmod=755 entrypoint.sh /usr/local/bin/
COPY redis.conf /etc/redis/

#hadolint global ignore=DL3064
ENV REDIS_USERNAME=redis
ENV REDIS_PASSWORD_SECRET_FILE=/run/secrets/redis_password
ENV REDIS_PRIVATE_KEY_PASSWORD_SECRET=/run/secrets/redis_private_key_password
# Enable TLS encryption, on | off.
ENV REDIS_ENCRYPTION=off
# Check client certificates: yes, no or optional.
ENV TLS_AUTH_CLIENT=yes

ENTRYPOINT [ "entrypoint.sh" ]
