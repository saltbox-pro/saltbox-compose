#!/bin/env python3

import sys

from datetime import datetime, timedelta, UTC
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


RFC5280_UNDEFINED_NOT_AFTER = datetime(
    year=9999,
    month=12,
    day=31,
    hour=23,
    minute=59,
    second=59,
    tzinfo=UTC
)


class MakeCertError(RuntimeError):
    ...


def write(data: bytes, path: Path) -> None:
    if path.exists():
        raise MakeCertError(f'Path {path} already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as file:
        file.write(data)


def create_key() -> rsa.RSAPrivateKey:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = Path('certs/key.pem')
    key_data = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(b'passphrase'),
    )
    write(key_data, path)
    print('RSA private key has been created')
    return key


def create_cert(
        relative_distinguished_name: x509.RelativeDistinguishedName,
        key: rsa.RSAPrivateKey,
        not_valid_after_days=None):
    subject = issuer = x509.Name(relative_distinguished_name)

    now = datetime.now(UTC)
    not_valid_after = RFC5280_UNDEFINED_NOT_AFTER
    if not_valid_after_days is not None:
        not_valid_after = now + timedelta(days=not_valid_after_days)

    alternative_name = x509.SubjectAlternativeName([x509.DNSName('localhost')])

    cert = x509.CertificateBuilder()\
        .subject_name(subject).issuer_name(issuer)\
        .public_key(key.public_key())\
        .serial_number(x509.random_serial_number())\
        .not_valid_before(now)\
        .not_valid_after(not_valid_after)\
        .add_extension(alternative_name, critical=False)\
        .sign(key, hashes.SHA256())

    cert_data = cert.public_bytes(serialization.Encoding.PEM)
    write(cert_data, Path('certs/certificate.pem'))
    print(f'Certificate for {relative_distinguished_name.rfc4514_string()} has been created')


if __name__ == '__main__':
    try:
        key = create_key()
        rdn = x509.RelativeDistinguishedName([
            x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'California'),
            x509.NameAttribute(NameOID.LOCALITY_NAME, 'San Francisco'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'My Company'),
            x509.NameAttribute(NameOID.COMMON_NAME, 'mysite.com'),
        ])
        create_cert(rdn, key)
    except MakeCertError as err:
        print(err, file=sys.stderr)
        exit(1)
