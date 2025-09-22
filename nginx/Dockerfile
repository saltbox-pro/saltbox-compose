FROM registry.altlinux.org/alt/alt:p11 AS base
LABEL version='0.2'
EXPOSE 80

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y gettext nginx
EOF

COPY nginx.conf /etc/nginx/
COPY --chmod=755 entrypoint.sh /docker/
COPY --chmod=755 10-nginx-tune.sh 20-process_templates.sh /docker/entrypoint.d/
COPY 00-override.conf /etc/nginx/conf-enabled.d/

ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["nginx"]
STOPSIGNAL SIGQUIT

ENV NGINX_WORKER_PROCESSES=auto
ENV NGINX_WORKER_CPU_AFFINITY=auto
