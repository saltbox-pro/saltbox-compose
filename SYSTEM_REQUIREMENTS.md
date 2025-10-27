# System requirements consideration

Approximate starer minimal for 500 hosts intallation is 32 vCPU, 32 GB RAM, 120
GB SSD.

> Lists are acutal on Oct 2025

Total consumption of an empty instance is 2.5 GB RAM as of Compose `stats`.

Most loaded components are marked with __[*]__

- Keycloak \~512MB RAM
- PortgreSQL 16 \~2GB RAM
- __[*]__ MongoDB 7 \~4GB RAM
- __[*]__ OPA latest \~512 MB RAM
- Nginx for proxy
- 4 × Nginx based frontends
- RabbitMQ 4 vCPU 4 GB RAM
- __[*]__ 2 × Redis 7 2 vCPU 4 GB RAM
- __[*]__ SaltStack Master
- sshd
- __[*]__ FastAPI + FastStream backend
- __[*]__ Taskiq workers
- FastAPI Gateway backend


Inventory proprietary module:

- FastAPI + FastStream backend
- 1 × Nginx based frontend
- MongoDB 7

Scheduler properietary module:

- FastAPI + FastStream backend
- 1 × Nginx based frontend
- MongoDB 7
- saltbox-scheduler-taskiq-scheduler
- saltbox-scheduler-taskiq-worker
