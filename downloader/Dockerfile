ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"

FROM "$BASE_IMG"
LABEL version="0.1"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes git
EOF

COPY --chmod=755 download.sh /usr/local/bin/
COPY download.d/ /root/download.d
ENTRYPOINT /usr/local/bin/download.sh

ENV SALT_REPO_URL=
ENV SALT_REPO_ENABLED=false
