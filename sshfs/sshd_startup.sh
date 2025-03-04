#! /bin/sh
set -e

trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

password="$(cat /run/secrets/sshfs_user_password)"
echo "$password" | passwd --stdin "$USERNAME"

chmod o+rwx "$STORAGE_PATH"

# Create host keys if not exists
ssh-keygen -A

# Test run
/usr/sbin/sshd -t

# Start server
/usr/sbin/sshd -D -e -p "$PORT"
