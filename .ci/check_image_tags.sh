#! /bin/bash
set -eux -o pipefail

extra_env=''
paths="$(bin/install_saltbox.py --list-addons | jq -r '.[].base_dir')"
clone_dir=clone

rm -rf "$clone_dir"
mkdir -p "$clone_dir/saltbox-compose"
ln -sr ./* "$clone_dir/saltbox-compose"
cd "$clone_dir/saltbox-compose"

rm -f override.env
for repo in $paths; do
   url="${GITLAB_INSTANCE_URL}/saltbox/${repo}"
   git -C .. clone --depth=1 --branch=dev "$url"
   extra_env="${extra_env}:../${repo}/.env"
   echo "COMPOSE_FILE=\"\${COMPOSE_FILE}:../${repo}/compose.yaml\"" >> override.env
done

echo "_UPDATE_AND_RUN_EXTRA_ENV_FILES=\"${extra_env#:}\"" >> override.env
cat override.env

bin/image_tags.py check
