# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Types of changes: Added, Changed, Deprecated, Removed, Fixed, Security.

__Some changes are breaking__. Cleanup Keycloak database before update
if possible and purge browser redirects.

## [Unreleased] - YYYY-MM-DD

### Added
- `install_saltbox_migrations.py` helper script.
- `install_saltbox.py` uses `install_saltbox_migrations.py` to install
  `Migrations` as an addon.
- `install_saltbox.py`: reads `compability_level` from `.installer.json` file
  in every repo to guarantee to work with compatible refs only.

### Changed

- `make_secrets.py`: flag `--output-dir` allows to work with an arbitrary
  output directory.

### Fixed

- `install_saltbox.py`: ignored `OVERRIDE` positional args.
- `install_saltbox.py`: add `--addons=NONE` option.

### Removed

## [0.2.0] - 2026-04-06

### Added

- Validation of `.env` checks for "unknown variables" (usually misstypes on
  overriding). Unknown variables means not specified in `base.env` and external
  dotenv files.
- `install_saltbox.py` script to simplify startup.
- `update_and_run.sh` flag `--no-progress` to hide dynamic progress-bars.
- `update_and_run.sh` on success writes Salt.Box URL also.
- Check for `REDIS_SALT_OUTER_SOCKET` deprecated var.
- `get_ca.sh` script to obtain `ca.crt` and optionally inject into Firefox.
- `./bin/make_secrets.py` has now `--explicit VAL=NAME` arg to set a secret value from
  cmdline.
- `base.env`: flags to enable/disable additional modules.

### Changed

- Rewrite `validate_dotenv.sh` script with Python.
- `./bin/update_and_run.sh`: more clear error on dockerd socket connection fail
and on missing `docker` command.
- Rename `example.env` -> `base.env` to be more clear. Keep symlink for
  compability.
- `git_pull_dev_repos.py`: more precise Git repositories detection in
  `service[].volumes.source` values.
- Service `proxy`: certificate has now `proxy` DNS alt name.
- `./bin/update_and_run.sh`: flag `--drop-data` now invokes `--remove-orphans`
  for better cleanup.
- Keycloak: realm is disabled while initial setup is going.
- `sshfs_file_manager` moved to a dedicated `saltbox-filebrowser-compose` repository.

### Fixed

- `./bin/update_and_run.sh` does not ask for `sudo` password with `--no-root`
flag.
- Unmatch `fi` in `kc_assign_user_to_group` function in `create-realm-common.sh`.
- `./bin/update_and_run.sh`: fix `git_pull_dev_repos.py` call with error when
  `.env` file does not exist.
- `git_pull_dev_repos.py`: ignore possible `PermissionError` on volume sources
  for Python<3.14.
- Nginx configuration: some potential problems has been eliminated.
- `proxy` service now has no dependencies.

### Removed

- Stale `compose-frontend-dev.yaml` override.

## [0.1.2] - 2025-12-22

### Added

- `./bin/check_image_tag.sh` helper script to check available tags.
- `migrator` user of SSHFS.
- Experimental `sshfs_file_manager`.

### Changed

- Decrease required by scripts Python version to `3.7.3`.

### Fixed

- RabbitMQ port forwarding.

## [0.1.1] - 2025-11-15

### Added

- `./bin/make_secrets.py` now reads config from JSON files.
- `_UPDATE_AND_RUN_EXTRA_SECRETS_CONFS` var allows to attach configs for
`make_secrets.py` from external modules.

### Changed

- Custom MongoDB ALT Linux based image.
- Switch MongoDB to replica set.
- Better MongoDB containers healthcheck.
- Pre-built proxy image.
- No more PyYAML requirement for scripts.
- Update Redis image due to vulnerability fix.

### Removed

- Remove metric related services.
- `BACKEND_HTTP_PORT` and `MONGO_PORT` variables.

## [0.1.0] - 2025-09-30

### Added

- Salt.Box Gateway service which coordinates HTTP communications.
- `SALT_FUNC_REPO_URL` with default repository URL to environment configuration
- Centralized logging with Graphana.
- `bin/update_and_run.sh`: `--only-env`, `--only-update` flags for more
  selective execution.
- `BACKEND_LOG_LEVEL` variable.
- `SALTBOX_BRIDGE_LOG_LEVEL` variable.
- `bin/update_and_run.sh`: success message with default admin credentials.
- `bin/update_and_run.sh`: `git pull` for Compose and connected modules repositories if applicable.
- `bin/update_and_run.sh`: retries for `docker compose pull`.
- `bin/update_and_run.sh`: `--no-root` flag to run as a regular user.
- `bin/update_and_run.sh`: handle `_UPDATE_AND_RUN_EXTRA_ENV_FILES` list
variable from `.env` to connect outer dotenv files easily.
- `./bin/sb-exec.sh`, `./bin/sb-compose.sh` helper scripts.
- Check `.env` for deprecated variables.
- Create private certificate for main web server, related new variables:
`WEB_SERVER_SSL_ALT_NAMES_DNS`, `WEB_SERVER_SSL_ALT_NAMES_IP`.
- Nginx workers tuning, related new variables: `WEB_SERVER_WORKER_PROCESSES`,
`WEB_SERVER_WORKER_CPU_AFFINITY`.

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
- Deleted variables: `WEB_SERVER_SCHEME`, `WEB_SERVER_WS_SCHEME`.

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
