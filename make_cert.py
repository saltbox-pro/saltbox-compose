#!/bin/env python3
# flake8: noqa: E501

##
## Requires python-cryptography >= 42
##

from __future__ import annotations

import sys

from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import TypeVar

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

KeyType = TypeVar('KeyType', rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey)


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


def save_key(key: KeyType, save_to: Path, passphrase: None | str = None) -> None:
    encryption_algorithm: serialization.KeySerializationEncryption = serialization.NoEncryption()

    if passphrase:
        encryption_algorithm = serialization.BestAvailableEncryption(passphrase.encode())

    key_data = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=encryption_algorithm,
    )
    write(key_data, save_to)

def save_cert(cert: x509.Certificate, save_to: Path) -> None:
    cert_data = cert.public_bytes(serialization.Encoding.PEM)
    write(cert_data, save_to)

def create_rsa_key(key_size=2048) -> rsa.RSAPrivateKey:
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    print('RSA private key has been created')
    return key


def create_ec_key() -> ec.EllipticCurvePrivateKey:
    key = ec.generate_private_key(ec.SECP256R1())
    print('Elliptic curve private key has been created')
    return key


def create_cert(
    save_to: None | Path,
    relative_distinguished_name: x509.RelativeDistinguishedName,
    key: KeyType,
    not_valid_after_days=None
) -> x509.Certificate:

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

    print(f'Certificate for {relative_distinguished_name.rfc4514_string()} has been created')
    return cert


if __name__ == '__main__':
    key_path = Path('certs/redis.key')
    cert_path = Path('certs/redis.crt')
    try:
        key = create_rsa_key()
        save_key(key, save_to=key_path)
        rdn = x509.RelativeDistinguishedName([
            x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'California'),
            x509.NameAttribute(NameOID.LOCALITY_NAME, 'San Francisco'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'My Company'),
            x509.NameAttribute(NameOID.COMMON_NAME, 'mysite'),
        ])
        cert = create_cert(save_to=cert_path, relative_distinguished_name=rdn, key=key)
        save_cert(cert, save_to=cert_path)
    except MakeCertError as err:
        print(err, file=sys.stderr)
        exit(1)
