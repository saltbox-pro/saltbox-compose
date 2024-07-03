# FastMS Compose

## Download

Get repository with submodules:

```bash
git clone --recursive
```

To update all submodules to latest version:

```bash
git submodule update --recursive --remote
```

## Build images

To build clean images use command:
```bash
sudo docker compose -f compose.yaml build --no-cache
```

`--no-cache` guarantees build with last versions of dependencies.


## Run

To build and run in development mode:

```bash
sudo docker compose -f compose.yaml -f compose-dev-override.yaml up --build --watch
```

`--build` flag rebuilds images, `--watch` flag rebuilds some images on src files
changes. `compose-dev-override.yaml` exposes additional ports.

To fix problems on start run before:

```bash
sudo docker system prune --force
```
