#! /bin/bash
set -e

declare -r override_env='override.env'
declare -r env_file='.env'
declare -r scheduler_env='../saltbox-scheduler-compose/.env'
declare -r inventory_env='../saltbox-inventory-compose/.env'

function warn() {
  1>&2 echo "$@"
}

# Добавляем значение по умолчанию для force_flag, если не задано
: "${force_flag:=1}"

if [ -f "$env_file" ]; then
  if [ "$force_flag" = 0 ]; then
    read -p "File '$env_file' already exists, overwrite? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      rm "$env_file"
    else
      warn "Using existing '$env_file'"
    fi
  else
    rm "$env_file"
  fi
fi

if [ ! -f "$env_file" ]; then
  cat example.env > "$env_file"

  # Добавляем содержимое scheduler_env, если файл существует
  if [ -f "$scheduler_env" ]; then
    cat "$scheduler_env" >> "$env_file"
  else
    warn "No $scheduler_env file, skipping"
  fi

  # Добавляем содержимое inventory_env, если файл существует
  if [ -f "$inventory_env" ]; then
    cat "$inventory_env" >> "$env_file"
  else
    warn "No $inventory_env file, skipping"
  fi

  # Добавляем override_env, если файл существует
  if [ -f "$override_env" ]; then
    cat "$override_env" >> "$env_file"
  else
    warn "No $override_env file, using defaults"
  fi

  chown "$(stat -c %u:%g .)" "$env_file"
  echo "New $env_file has been created"
fi
