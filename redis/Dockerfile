FROM redis:7-alpine
LABEL version='0.1'

COPY entrypoint.sh /usr/local/bin/
ENV REDIS_USERNAME default

ENTRYPOINT ["entrypoint.sh"]
