ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"

#hadolint global ignore=DL3006,DL3015,DL3008
FROM "$BASE_IMG" AS base
LABEL version="4.0"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes curl=8.23.0-alt1 \
                      openssh-server=9.6p1-alt7 \
                      passwd=1.0.14-alt1 \
                      python3=3.12.13-alt1 \
                      rsync=3.2.7-alt7 \
                      systemd- \
                      udev- \
                      dbus-
apt-get autoremove --yes --purge
EOF

COPY sshd_config /etc/openssh/
COPY --chmod=755 sshd_entrypoint.py /usr/local/bin/

ENV PORT=1022
ENV USERS_FILE='/mnt/users.json'
ENV AUTHORIZED_KEYS_URL='http://example.local/authorized_keys/${user}'
EXPOSE $PORT

ENTRYPOINT [ "/usr/local/bin/sshd_entrypoint.py" ]
