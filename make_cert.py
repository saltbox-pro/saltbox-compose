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
DEFAULT_CA_KEY_USAGE={
    'digital_signature': True,
    'content_commitment': False,
    'key_encipherment': False,
    'data_encipherment': False,
    'key_agreement': False,
    'key_cert_sign': True,
    'crl_sign': True,
    'encipher_only': False,
    'decipher_only': False,
}
DEFAULT_END_ENTITY_KEY_USAGE = DEFAULT_CA_KEY_USAGE | {
    'key_encipherment': True,
    'key_cert_sign': False,
}


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
    subject: x509.Name,
    key: KeyType,
    root_cert: None | x509.Certificate = None,
    root_key: None | KeyType = None,
    not_valid_after_days=None
) -> x509.Certificate:
    """
    :param ca_cert: root certificate, create root cert if None
    """
    is_root = root_cert is None
    if is_root:
        issuer = subject
        key_usage = x509.KeyUsage(**DEFAULT_CA_KEY_USAGE)
        sign_key = key
    else:
        issuer = ca_cert.subject
        key_usage = x509.KeyUsage(**DEFAULT_END_ENTITY_KEY_USAGE)
        if not root_key:
            raise MakeCertError('Missing root key for singing')
        sign_key = root_key

    key_identifier = x509.SubjectKeyIdentifier.from_public_key(key.public_key())

    now = datetime.now(UTC)
    not_valid_after = RFC5280_UNDEFINED_NOT_AFTER
    if not_valid_after_days is not None:
        not_valid_after = now + timedelta(days=not_valid_after_days)

    alternative_name = x509.SubjectAlternativeName([x509.DNSName('localhost')])
    #alternative_name = x509.IPAddress([x509.IPAddress('')])
    # FIXME .add_extension(alternative_name, critical=False)\

    builder = x509.CertificateBuilder()\
        .subject_name(subject)\
        .issuer_name(issuer)\
        .public_key(key.public_key())\
        .serial_number(x509.random_serial_number())\
        .not_valid_before(now)\
        .not_valid_after(not_valid_after)\
        .add_extension(x509.BasicConstraints(ca=is_root, path_length=None), critical=True)\
        .add_extension(key_usage, critical=True)\
        .add_extension(key_identifier, critical=False)

    if root_cert:
        ext_key_usage = x509.ExtendedKeyUsage([
            x509.ExtendedKeyUsageOID.CLIENT_AUTH,
            x509.ExtendedKeyUsageOID.SERVER_AUTH,
        ])
        ext = root_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
        auth_key_indent = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ext)
        builder = builder\
            .add_extension(ext_key_usage, critical=False)\
            .add_extension(auth_key_indent, critical=False)

    cert = builder.sign(key, hashes.SHA256())

    type_srt = 'Root' if is_root else 'Endpoint'
    print(f'{type_srt} certificate for {subject.rfc4514_string()} has been created')
    return cert


if __name__ == '__main__':
    certs_dir = Path('certs/')
    # TODO config: overwrite
    # TODO config: Name
    subject = x509.Name(x509.RelativeDistinguishedName([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'California'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, 'San Francisco'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'My Company'),
        x509.NameAttribute(NameOID.COMMON_NAME, 'mysite'),
    ]))
    try:
        ca_key = create_ec_key()
        save_key(ca_key, save_to=certs_dir / 'ca.key')
        ca_cert = create_cert(subject=subject, key=ca_key)
        save_cert(ca_cert, save_to=certs_dir / 'ca.crt')
        ee_key = create_ec_key()
        save_key(ee_key, save_to=certs_dir / 'redis.key')
        ee_cert = create_cert(subject=subject, key=ee_key, root_cert=ca_cert, root_key=ca_key)
        save_cert(ee_cert, save_to=certs_dir / 'redis.crt')

        # TODO
        #from cryptography.x509 import DNSName
        #from cryptography.x509.verification import PolicyBuilder, Store
        #store = Store([ca_cert])
        #builder = PolicyBuilder().store(store)
        #verifier = builder.build_server_verifier(DNSName("localhost"))
        #chain = verifier.verify(ee_cert, [ca_cert])
        #print(len(chain))
    except MakeCertError as err:
        print(f'ERROR: {err}', file=sys.stderr)
        exit(1)
