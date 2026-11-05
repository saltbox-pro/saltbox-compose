ARG BASE_IMAGE='registry.altlinux.org/alt/alt:p11'

#hadolint global ignore=DL3006,DL3015
FROM "$BASE_IMAGE"

LABEL name="make-certs"
LABEL version="0.3"

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
apt-get install --yes glibc-pthread=2.38.0.223.f053ff-alt1.p11.1 \
                      python3=3.12.13-alt1 \
                      python3-module-jinja2=3.1.6-alt1 \
                      python3-module-pip=26.1.2-alt1
pip3 install "make-certs==${MAKE_CERTS_VERSION}" --index-url "$PIP_INDEX_URL"
apt-get remove --auto-remove --yes python3-module-pip
EOF

COPY --chmod=755 entrypoint/* /docker/

WORKDIR /root/ 
ENV STATE_FILE=/root/hier.state
ENV HIER_TEMPLATE=/root/hier.yaml.jinja2
