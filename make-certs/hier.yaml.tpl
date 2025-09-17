---

names:
  saltbox:
    country_name: RU
    state_or_province_name: Central Federal District
    locality_name: Moscow
    organization_name: Salt.Box
    common_name: saltbox
  redis-salt:
    country_name: RU
    state_or_province_name: Central Federal District
    locality_name: Moscow
    organization_name: Salt.Box
    common_name: redis-salt
  proxy:
    country_name: RU
    state_or_province_name: Central Federal District
    locality_name: Moscow
    organization_name: Salt.Box
    common_name: localhost

certs:
  /mnt/redis_certs/ca.crt:
    subject: saltbox
    not_valid_after_days: null
    key_password: '${CA_KEY_PASSWORD}'
    basic_constraints:
      ca: true
      path_length: 0  # No further CA certificates
    issue:
      /mnt/redis_certs/redis.crt:
        subject: redis-salt
        not_valid_after_days: null
        key_password: '${REDIS_KEY_PASSWORD}'
        basic_constraints:
          ca: false
          path_length: null
        alternative_names_ip:
          - '127.0.0.1'
        alternative_names_dns:
          - localhost
          - redis-salt
        extended_key_usage:
          server: true
          client: false
      /mnt/proxy_certs/proxy.crt:
        subject: proxy
        not_valid_after_days: null
        key_password: null
        basic_constraints:
          ca: false
          path_length: null
        alternative_names_ip:
          - '127.0.0.1'
        alternative_names_dns:
          - '${PROXY_ALT_NAME}'
          - localhost
        extended_key_usage:
          server: true
          client: false

# vi: syn=yaml
