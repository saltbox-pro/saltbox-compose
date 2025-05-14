ARG BASE_IMG="registry.altlinux.org/alt/alt:p11"
FROM "$BASE_IMG"
LABEL version="3.0"

RUN \
  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
<<EOF
set -e
mkdir --parents /var/cache/apt/archives/partial/ /var/lib/apt/lists/partial/
apt-get update
apt-get install --yes curl git openssh-server passwd python3 systemd- udev- dbus-
apt-get autoremove --yes --purge
EOF

COPY sshd_config /etc/openssh/
COPY --chmod=755 sshd_entrypoint.py /usr/local/bin/

ENV PORT=1022
ENV USERS_FILE='/mnt/users.json'
ENV AUTHORIZED_KEYS_URL='http://example.local/authorized_keys/${user}'
EXPOSE $PORT

ENTRYPOINT ["/usr/local/bin/sshd_entrypoint.py"]
