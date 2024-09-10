FROM nginx:stable-alpine

RUN \
  --mount=type=bind,target=/mnt/ \
<<EOF
rm /etc/nginx/conf.d/default.conf
cp /mnt/fastms.conf /etc/nginx/conf.d/
EOF
