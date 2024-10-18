> **ATTENTION!** Project is on the early stage and is not ready for usage.

# FastMS Compose

## Download

Get repository for first time:

```bash
git submodule update --init --recursive
```

Get repository with submodules:

```bash
git clone --recursive
```

Update repository and top level submodules to fixed version:

```bash
git pull --recurse-submodules
```

Update repository and top level submodules to latest version:

```bash
git pull
git submodule update --remote
```

## Build images

To build clean images use command:

```bash
sudo docker compose -f compose.yaml build --no-cache
```

`--no-cache` guarantees build with last versions of dependencies.

## Run

Initially secrets must be created in the `./secrets/` subdirectory. It may be
done with helper script:

```bash
./make_secrets.py
```

To build and run in development mode:

**ATTENTION!** Do not use development mode on production environments cause it
may change the data.

```bash
sudo docker compose -f compose.yaml -f compose-dev-override.yaml up --build --watch
```

`--build` flag rebuilds images, `--watch` flag rebuilds some images on src files
changes. `compose-dev-override.yaml` exposes additional ports.

## Cleanup

After changes created containers and volumes may become incompatible with
current code without special migrations.

To fix startup problems on developement environment stop containters with `^C`
and make them down:

```bash
sudo docker compose -f compose.yaml -f compose-dev-override.yaml down --volumes
```

**ATTENTION!** The `--volumes` flag will purge attached volumes and will lead
to data lost. Be sure to not lost production data.

While changins code and configs new layers and other objects are created. To
free resources run time to time the following command:

```bash
sudo docker system prune --force
```

Usually it is safe and deletes only stale data.

## Development

### Redis: channels

Hash name shoud be in form of `OBJ_TYPE:{ID}:DATA_TYPE` e.g.
`minion:{MID}:grains`. Also mention single form of obj type and plural form for
data type, because there are many values for the object.

### Keycloak

Keycloak for `admin` user (password in file `./secrets/keycloak_admin_password`): http://localhost/auth/keycloak/
