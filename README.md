# Salt.Box Compose

## About Salt.Box

Salt.Box is a configuration management system wich extends
[SaltStack](https://saltproject.io/) with web UI.

Look for user documentation on [saltbox.pro](https://saltbox.pro).

## Requirements

- Docker Engine >= 25.0 _(due to healthcheck feature)_
- Docker Compose >= 2.20.2
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

## Working behind a reverse proxy

Currently to make web interface work properly for remote hosts HTTP connection
must have SSL termination. Usual way to achieve this is to use Nginx web
server as a HTTP reverse proxy and terminate SSL on it.

First, be sure to set `WEB_SERVER_OUTER_SOCKET` to match `server_name` and port
of the reverse proxy.

Nginx may be installed on the same host with Salt.Box, or on another one. In
the last case be sure the Salt.Box is available for the Nginx host e.g. with
command `curl http://<SALTBOX_HOST>:<SALTBOX_WEB_SERVER_PORT>/auth/keycloak/realms/salt.box/.well-known/openid-configuration`. It should return long JSON response.

An example Nginx config following. Remember to edit `< ... >` placeholders and
check config with `sudo nginx -t`.

```nginx
server {
  server_name <NAME>;
  client_max_body_size 256m;

  access_log /var/log/nginx/saltbox_access.log;
  error_log /var/log/nginx/saltbox_error.log;

  location / {
    add_header X-Frame-Options 'SAMEORIGIN';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection ‘upgrade’;

    proxy_pass http://<SALTBOX_HOST>:<SALTBOX_WEB_SERVER_PORT>;
  }

  listen 443 ssl http2;
  ssl_certificate <PATH_TO_CERT>;
  ssl_certificate_key <PATH_TO_CERT_KEY>;
  < OTHER SSL SETTTINGS DEPENDS ON CERT>
}

server {
  server_name <NAME>;
  listen 80;
  return 301 https://$host$request_uri;
}
```

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

### Cleanup all data

After changes created containers and volumes may become incompatible with
current code without special migrations.

To fix startup problems on developement environment stop containters with `^C`
and make them down:

```bash
sudo docker compose -f compose.yaml -f compose-dev-override.yaml down --volumes
```

**ATTENTION!** The `--volumes` flag will purge attached volumes and will lead
to data lost. Be sure to not lost production data.

### Cleanup Keycloak data only

Run followin commands:

```bash
sudo docker compose down
sudo docker compose down keycloak-db --volume
```

On the next start the realm will be recreated.

### Cleanup stale Docker stuff

While changing code and configs new layers and other objects are created. To
free resources run time to time the following command:

```bash
sudo docker system prune --force
```

Usually it is safe and deletes only stale data.

## Development agreements

### Docker Compose

- `healthcheck.{interval,timeout,start_period,start_interval}` keywords
introduced in Docker Compose 2.20.2, it is a __current version limiter__.
- `develop` specification introduced in Docker Compose 2.22.0, it should be
avoided in the main [`compose.yaml`](compose.yaml) file.

### Redis: channels

Hash name shoud be in form of `OBJ_TYPE:{ID}:DATA_TYPE` e.g.
`minion:{MID}:grains`. Also mention single form of obj type and plural form for
data type, because there are many values for the object.

### Keycloak

Keycloak administrative interface: http://localhost/auth/keycloak/.
User `admin`, password from `./secrets/keycloak_admin_password`.
