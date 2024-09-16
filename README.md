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

To fix problems on start run before:

```bash
sudo docker system prune --force
```

## Development

### Redis: channels

Hash name shoud be in form of `OBJ_TYPE:{ID}:DATA_TYPE` e.g.
`minion:{MID}:grains`. Also mention single form of obj type and plural form for
data type, because there are many values for the object.

### Keycloak: export realm

1. Create and tune a realm with admin panel.
1. Stop `keycloak` container. `keycloak-db` container must be ran.
1. Exec command:

```bash
sudo docker compose run --volume './:/mnt/' \
    keycloak export --optimized --file /mnt/realm_fastms.json --realm fastms
```

Then delete policy nodes with deprecated `"type": "js"`:
```bash
jq --indent 2 'del(.clients.[].authorizationSettings)' \
    tmp.json > keycloak/realm_fastms.json
rm tmp.json
```

Realm JSON file will be updated and formatted.
