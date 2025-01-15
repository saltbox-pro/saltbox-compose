# Nginx image

ALT Linux based Nginx image supposed to be used as a part of salt.box system
and inherits some conceptions of the official Nginx Docker image.

- Respective __configs__ can be placed into `/etc/nginx/sites-enabled.d/` and
  `/etc/nginx/conf-enabled.d/`.
- Site config __templates__ with the `.template` additional suffix can be
  placed into `/etc/nginx/templates/`. Environment variables will be
  substituted with `envsubst` and rendered configs will be flatly place into
  `/etc/nginx/sites-enabled.d/`.
- Additional `*.sh` scripts can be placed into `/docker/entrypoint.d/` and will
  be sourced by default with the `entrypoint.sh` startup Bash script.
