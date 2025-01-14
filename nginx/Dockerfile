FROM registry.altlinux.org/alt/alt:p11 AS base
LABEL version='0.1'
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

COPY --chmod=755 entrypoint.sh /docker/
COPY --chmod=755 20-process_templates.sh /docker/entrypoint.d/
COPY override.conf /etc/nginx/conf-enabled.d/
RUN sed --in-place 's/\(http\s*{\)/\1\n\taccess_log off;/' /etc/nginx/nginx.conf

ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["nginx"]
STOPSIGNAL SIGQUIT
