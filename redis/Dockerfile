FROM redis:7-alpine
LABEL version='0.1'

COPY entrypoint.sh /usr/local/bin/
COPY redis.conf /etc/redis/
ENV REDIS_USERNAME=redis
# Check client certificates: yes, no or optional
ENV TLS_AUTH_CLIENT=yes

ENTRYPOINT ["entrypoint.sh"]
