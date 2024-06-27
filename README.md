# FastMS Compose

## Run

To run in developement mode:

```bash
sudo docker compose -f compose.yaml -f compose-dev-override.yaml up --build --watch
```

`--build` flag rebuilds images, `--watch` flag rebuilds some images on src files
changes. `compose-dev-override.yaml` exposes additional ports.

To fix problems on start run before:

```bash
sudo docker system prune --force
```
