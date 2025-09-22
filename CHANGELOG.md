# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Types of changes: Added, Changed, Deprecated, Removed, Fixed, Security.

## [Unreleased]

__Some changes are breaking__. Cleanup Keycloak database before update
if possible and purge browser redirects.

### Added

- `SALT_FUNC_REPO_URL` with default repository URL to environment configuration
- `bin/update_and_run.sh`: `--only-env`, `--only-update` flags for more
  selective execution.
- `BACKEND_LOG_LEVEL` variable.
- `SALTBOX_BRIDGE_LOG_LEVEL` variable.
- `bin/update_and_run.sh`: success message with default admin credentials.
- `bin/update_and_run.sh`: `git pull` for Compose and connected modules repositories if applicable.
- `bin/update_and_run.sh`: retries for `docker compose pull`.
- `bin/update_and_run.sh`: `--no-root` flag to run as a regular user.
- `./bin/sb-exec.sh`, `./bin/sb-compose.sh` helper scripts.
- Check `.env` for deprecated variables.
- Create private certificate for main web server.
- Nginx workers tuning.

### Changed

- Rename `KEYCLOAK_{USER,ADMIN}_*` variables to `SALTBOX_{USER,ADMIN}_*`
  to be more clear.
- Each secret now is bound to an unique secret file.
- Change some values to be more consistent to product name.
- ALT based `make-certs` image.
- Make `make-certs` not depends on image from other repo.
- Make `make-certs` image generic.
- `bin/update_and_run.sh`: run as root only Docker commands, run with `sudo` is
  optional now.

### Fixed

- `bin/update_and_run.sh`: overwriting `.env` even on negative answer.

### Removed

- No-SSL HTTP for the web UI.

## [0.0.2] - 2025-05-16

## Added

- New options for `./bin/update_and_run.sh` script.
- `./bin/update_and_run.sh` makes secrets.
- Tags for all inner images.
- `users.json` config for `sshfs` image to recreate users on very start.
- `SHOW_DOCS` env variable.
- `./bin/merge_env.sh` helper script.
- `sshfs` obtain authorized keys with HTTP GET on every connection.

## Updated

- Synchronize with components.
- Documentation.
- Autotests config.

## Deprecated

- `BACKEND_HOST` env variable.

## [0.0.1] - 2025-04-23

### Added

- Initial version tag.
