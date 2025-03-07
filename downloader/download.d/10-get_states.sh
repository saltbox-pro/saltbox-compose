#! /bin/sh
set -e

if [ "$SALT_REPO_ENABLED" != 'true' ]; then
  echo "SALT_REPO_ENABLED!='true', skip donwloading"
  exit 0
fi

repo_url="${SALT_REPO_URL}"
repo_dir='/srv/salt/repo'

if [ ! -d "$repo_dir" ]; then
  echo 'Clonning remote repo now'
  git clone --depth=1 "$repo_url" /srv/salt/repo
else
  echo 'Local repo exists, trying to update now'
  cd "$repo_dir"
  git pull
fi
