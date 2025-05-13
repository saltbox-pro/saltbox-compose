#! /bin/bash
set -e

override_env='override.env'
env_file='.env'
force_flag=1

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

if [ -f "$override_env" ]; then
  cat "$override_env" >> "$env_file"
else
  warn "No $override_env file, using defaults"
fi
