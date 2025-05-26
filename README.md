# Salt.Box Compose

## About Salt.Box

Salt.Box is a configuration management system wich extends
[SaltStack](https://saltproject.io/) with web UI.

Look for user documentation on [saltbox.pro](https://saltbox.pro).

## Requirements

- Docker Engine >= 25.0 _(due to healthcheck feature)_
- Docker Compose >= 2.22.0
- Python >= 3.9 _(for `./bin/make_secrets.py`)_

## Prepare

Initially secrets must be created in the `./secrets/` subdirectory. It may be
done with helper script:

```bash
./bin/make_secrets.py
```

Make copy of [`example.env`](example.env) file named `.env`. Tune it before run.

To make the UI available on hostname or address other than `localhost` override
variables those defaults are `localhost`.

## Helper script to start

Easy way to run the system is execute:
```bash
sudo ./bin/update_and_run.sh
```

Helper script:
- Merges `example.env` and `override.env` (if exists) into `.env` config.
- Makes secrets.
- Updates images.
- Runs the Salt.Box instance.

Use `override.env` to redefine `example.env` default values.

Use `-h` or `--help` flag to look script options.

Another way is to go step-by-step.

## Run step-by-step

```bash
sudo docker compose up --build
```

**ATTENTION!** Check there are no warnings on not setted variables to avoid
confusing errors.

To update outer images:

```bash
sudo docker compose pull
```

than restart e.g. with `sudo docker compose down && sudo docker compose up -d`.

It is possible to pull images on start with an additional flag `sudo
docker compose up --build --pull=always`.

For production use following commands are recommended:

```bash
sudo sh -c "echo 'vm.overcommit_memory=1' > /etc/sysctl.d/saltbox.conf"
sudo sysctl -p /etc/sysctl.d/saltbox.conf
```

`vm.overcommit_memory=1` is a Redis requirement.

## Autotests

To run test suites enable `compose-autotests.yaml` in the local`.env` file.
Then execute:

```bash
sudo docker compose up autotests
```

Autotests depends on direct access to Keycloak API, so existing realm should be
recreated. As alternative the "Direct access grants" checkbox may be checked at
Keycloak client settings.

To prevent pulling a new image:

```bash
sudo docker compose up autotests --pull=never
```

## Dev mode

### Synopsis

Dev mode allows to build images instead of pulling pre-built and adds some
useful overrides.

Look at "Dev options" section of your [`example.env`](example.env) file copy.
To enable dev options uncomment required `COMPOSE_FILE=` lines. Than run
compose as usual.

Use `--watch` flag or toggle watch with `w` in attached mode to rebuld
dev-services on changes.

**ATTENTION!** Do not use development mode on production environments cause it
may change the data.

### Build images in dev mode

To build clean images use command with enabled `COMPOSE_FILE` overrides:

```bash
sudo docker compose build --no-cache
```

`--no-cache` guarantees build with latest dependencies.

### Connect to redis-salt Redis instance

Dev mode allows to connect to the Redis instance by URL
`rediss://localhost:6379` (SIC!). Since TLS is enabled client may skip
a certificate validation (option like `--insecure`) or use a CA certificate.
The last may be obtained with command:

```bash
sudo docker compose exec redis-salt cat /etc/redis/certs/ca.crt
```

### Dev minions

Dev mode provides amount of impersistent minions in replica mode. Look for
options in the [`example.env`](./example.env) file.

Dev minions does not keep their keys between restarts so keys will be dropped
on the master. Some operations may lead to lost minions. It that keys try the
following command, which should reconnect minions:

```bash
sudo docker compose restart salt-master
```

Note: `docker compose up --force-recreate salt-master` not regenerates
minions.

## Cleanup

### Cleanup data

After changes created containers and volumes may become incompatible with
current code without special migrations.

To fix startup problems on developement environment stop containters with `^C`
and make them down:

```bash
sudo docker compose -f compose.yaml -f compose-dev-override.yaml down --volumes
```

**ATTENTION!** The `--volumes` flag will purge attached volumes and will lead
to data lost. Be sure to not lost production data.

### Cleanup stale Docker stuff

While changing code and configs new layers and other objects are created. To
free resources run time to time the following command:

```bash
sudo docker system prune --force
```

Usually it is safe and deletes only stale data.

## Development agreements

### Redis: channels

Hash name shoud be in form of `OBJ_TYPE:{ID}:DATA_TYPE` e.g.
`minion:{MID}:grains`. Also mention single form of obj type and plural form for
data type, because there are many values for the object.

### Keycloak

Keycloak for `admin` user (password in file
`./secrets/keycloak_admin_password`): http://localhost/auth/keycloak/
