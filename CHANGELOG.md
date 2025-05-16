# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Types of changes: Added, Changed, Deprecated, Removed, Fixed, Security.

## [Unreleased]

### Added

- `SALT_FUNC_REPO_URL` with default repository url to environment configuration

### Changed

### Removed

## [0.0.2] - 2025-05-16

## Added

- New options for `./bin/update_and_run.sh` script.
- `./bin/update_and_run.sh` makes secrets.
- Tags for all inner images.
- `users.json` config for `sshfs` image to recreate users on very start.
- `SHOW_DOCS` env variable.
- `./bin/merge_env.sh` helper script.
- `sshfs` obtain authorized keys with HTTT GET on every connection.

## Updated

- Synchronize with components.
- Documentation.
- Autotests config.

## Deprecated

- `BACKEND_HOST` env variable.

## [0.0.1] - 2025-04-23

### Added

- Initial version tag.
