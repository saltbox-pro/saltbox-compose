#! /bin/bash
set -e

override_env='override.env'
env_file='.env'
usage_str="
Update images and run a Salt.Box Docker Compose based instance.

Usage: sudo ./bin/update_and_run.sh [-d|--detach] [-h|--help]

  -d|--detach\tDetach Docker Compose after start
  -f|--force\tRewrite with no confirmation
  -h|--help\tPrint this message
  -n|--no-pull\tDo not pull newer images from registry
"

warn() {
  1>&2 echo "$@"
}

err() {
  warn "$@"
  exit 1
}

up_args=('--remove-orphans')
force_flag=0
pull_flag=1

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -d|--detach) up_args+=('--detach') ;;
    -f|--force) force_flag=1 ;;
    -h|--help) printf "$usage_str" && exit 0 ;;
    -n|--no-pull) pull_flag=0 ;;
    *) err "Unknown option $i" ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  err "Root access required, try sudo $0"
fi

if [ -f "$env_file" ] && [ $force_flag = 0 ]; then
  read -p "File '$env_file' already exists, overwrite? (y/n): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm "$env_file"
  else
    warn "Using existing '$env_file'"
  fi
fi

cat example.env > "$env_file"

# shellcheck source=/dev/null
registry=$(
  source "$env_file"
  echo "$IMAGE_REGISTRY" | cut --delimiter '/' --fields 1
)

if [ -z "$registry" ]; then
  err "Failed to get registry from $env_file"
fi

if [ -f "$override_env" ]; then
  cat "$override_env" >> "$env_file"
else
  warn "No $override_env file, using defaults"
fi

chown "$(stat -c %u:%g .)" "$env_file"

if [ $pull_flag = 1 ]; then
  (set -x; docker login "$registry")
  (set -x; docker compose pull --ignore-buildable)
fi
(set -x; docker compose build)
(set -x; docker compose up "${up_args[@]}")
