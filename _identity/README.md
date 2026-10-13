# `_identity/` subdirectory

This subdirectory attached to Keycloak containers at `/etc/identity/` point to
attach domain controllers as external identities.

Following main file supposed to be placed inside:

1. `krb5.conf` Kerberos-compatible config
2. Keytab file. Path should be settend in GUI User Federation settings
   starting with `/etc/identity/`.
__WARN!__ permissions MUST be prohibitive.
3. Domain controller root certificates in `cacert/` sub(sub)directory to verify
   connection.
