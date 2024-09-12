FROM nginx:stable-alpine
LABEL version='0.1'

RUN \
  --mount=type=bind,target=/mnt/ \
<<EOF
rm /etc/nginx/conf.d/default.conf
mkdir -p /etc/nginx/templates/
cp /mnt/fastms.conf.template /etc/nginx/templates/
EOF
