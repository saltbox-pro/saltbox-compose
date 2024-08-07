# FastMS Compose

## Download

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

To build and run in development mode:

__ATTENTION!__ Do not use development mode on production environments cause it
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

Hash name shoud be in form of `OBJ_TYPE:{ID}:DATA_TYPE` e.g.
`minion:{MID}:grains`. Also mention single form of obj type and plural form for
data type, because there are many values for the object.
