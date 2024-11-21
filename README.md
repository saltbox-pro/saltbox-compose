> **ATTENTION!** Project is on the early stage and is not ready for usage.

# FastMS Compose

## Prepare

While project is private, login required to obtain the images.

  1. Create a personal token: on [GitLab instance](https://dev.altlab.su) your
     profile -> Edit profile -> Access tokens on the side menu. Add
     `read_registry` scope. Copy the
     token.
  1. Run `docker login registry.altlab.su`, use your username for login and the
     token value for password.
     **ATTENTION!** Token will be kept as plain text if you have no configured
     credential helper.

Initially secrets must be created in the `./secrets/` subdirectory. It may be
done with helper script:

```bash
./make_secrets.py
```

Make copy of [`example.env`](example.env) file named `.env`. Tune it, than run:

## Run

```bash
sudo docker compose up --build
```

For production use following commands are recommended:
```bash
sudo sh -c "echo 'vm.overcommit_memory=1' > /etc/sysctl.d/fastms.conf"
sudo sysctl -p /etc/sysctl.d/fastms.conf
```

`vm.overcommit_memory=1` is a Redis requirement.

## Dev mode

### Synopsis

Dev mode allows to build images instead of pulling pre-built and adds some
useful overrides.

Look at "Dev options" section of your [`example.env`](example.env) file copy. To
enable dev mode uncomment `COMPOSE_FILE=` line. Than run compose as usual.

**ATTENTION!** Do not use development mode on production environments cause it
may change the data.

### Build images in dev mode

To build clean images use command:

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
