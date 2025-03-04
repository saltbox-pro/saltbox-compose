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
apt-get install --yes openssh-server passwd systemd- udev- dbus-
apt-get autoremove --yes --purge
EOF


ENV USERNAME=salt-box
ENV STORAGE_PATH=/srv/sshfs/
RUN useradd \
  --shell /usr/sbin/nologin \
  --groups users \
  --home-dir "$STORAGE_PATH" --create-home \
  "$USERNAME"

ENV PORT=1022
EXPOSE $PORT

COPY sshd_config /etc/openssh/
COPY sshd_startup.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/sshd_startup.sh"]
