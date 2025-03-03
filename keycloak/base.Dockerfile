ARG BASE_IMG=registry.altlinux.org/alt/alt:p11

FROM "$BASE_IMG"
LABEL version='0.1'

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install -y keycloak
EOF
