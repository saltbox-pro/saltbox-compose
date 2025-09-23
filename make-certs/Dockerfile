ARG BASE_IMAGE='registry.altlinux.org/alt/alt:p11'
FROM "$BASE_IMAGE"
LABEL name='make-certs' version='0.1'
ARG MAKE_CERTS_VERSION='0.2.1'
ARG PIP_INDEX_URL='https://dev.saltbox.pro/api/v4/projects/8/packages/pypi/simple'
RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
  --mount=type=cache,target=/root/.cache/pip/ \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes glibc-pthread python3 python3-module-jinja2 python3-module-pip
pip3 install "make-certs==${MAKE_CERTS_VERSION}" --index-url "$PIP_INDEX_URL"
apt-get remove --auto-remove --yes python3-module-pip
EOF
WORKDIR /root/ 
