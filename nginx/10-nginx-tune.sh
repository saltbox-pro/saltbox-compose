#! /bin/sh

cat << EOF > /etc/nginx/conf-enabled.d/10-saltbox-tune.conf
worker_processes ${NGINX_WORKER_PROCESSES};
worker_cpu_affinity ${NGINX_WORKER_CPU_AFFINITY};
EOF
