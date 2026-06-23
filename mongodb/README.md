# Salt.Box MongoDB image

## Description

MongoDB image is like official one but has 1-node replica-set.

## Required variables

- `MONGOD_KEY_FILE` — path to secret file for replica-set mode.
- `MONGOD_REPLICA_SET` — replica-set name.
- `MONGO_ROOT_PASSWORD_FILE` — DB admin password file path.
- `MONGO_ROOT_USERNAME` — DB admin username.
- `MONGO_USER_PASSWORD_FILE` — DB user (application) password file path.
- `MONGO_USER_USERNAME` — DB user (application) name.
- `MONGO_EXPORTER_PASSWORD_FILE` — optional read-only user password file path.
- `MONGO_EXPORTER_USERNAME` — optional read-only user name.
