FROM nginx:stable-alpine
LABEL version='0.2'

RUN \
  --mount=type=bind,target=/mnt/ \
<<EOF
rm /etc/nginx/conf.d/default.conf
mkdir -p /etc/nginx/templates/
cp /mnt/salt-box.conf.template /etc/nginx/templates/
EOF

COPY 15-frontend-env.sh /docker-entrypoint.d/
