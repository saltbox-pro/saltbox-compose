#!/bin/env python3
# flake8: noqa: E501

##
## Requires python-cryptography >= 42, pyyaml
##

from __future__ import annotations

import argparse
import sys

from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

import yaml

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

KeyType = rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey


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


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='make_cert',
        description='Create x509 certificates heirarhy',
    )
    parser.add_argument('filename')
    return parser.parse_args()


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
    issuer_cert: None | x509.Certificate = None,
    signing_key: None | KeyType = None,
    not_valid_after_days=None
) -> x509.Certificate:
    """
    :param ca_cert: root certificate, create root cert if None
    """
    is_root = issuer_cert is None
    if issuer_cert is None:
        issuer = subject
        key_usage = x509.KeyUsage(**DEFAULT_CA_KEY_USAGE)
        signing_key = key
    else:
        issuer = issuer_cert.subject
        key_usage = x509.KeyUsage(**DEFAULT_END_ENTITY_KEY_USAGE)

    if not signing_key:
        raise MakeCertError('Missing root key for singing')

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

    if issuer_cert:
        ext_key_usage = x509.ExtendedKeyUsage([
            x509.ExtendedKeyUsageOID.CLIENT_AUTH,
            x509.ExtendedKeyUsageOID.SERVER_AUTH,
        ])
        # TODO  SubjectKeyInd
        ext = issuer_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
        auth_key_indent = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ext)
        builder = builder\
            .add_extension(ext_key_usage, critical=False)\
            .add_extension(auth_key_indent, critical=False)

    cert = builder.sign(signing_key, hashes.SHA256())

    type_srt = 'Root' if is_root else 'Endpoint'
    print(f'{type_srt} certificate for {subject.rfc4514_string()} has been created')
    return cert


def name_from_dict(data: dict[str, str]) -> x509.Name:
    attrs_list = []
    for k, val in data.items():
        attr_type = getattr(NameOID, k.upper())
        attr = x509.NameAttribute(attr_type, val)
        attrs_list.append(attr)
    return x509.Name(x509.RelativeDistinguishedName(attrs_list))


def cert_from_dict(
    cert_path: Path,
    options: dict[str, Any],
    subjects: dict[str, x509.Name],
    issuer_cert: None | x509.Certificate = None,
    signing_key: None | KeyType = None,
) -> None:
    print(f'Processing {cert_path} entry...')

    # TODO load if exists
    cert_dir = cert_path.parent
    key_path = cert_dir / f'{cert_path.stem}.key'
    key_type = options['key_type']

    if key_type == 'rsa':
        key: KeyType = create_rsa_key()
    elif key_type == 'ec':
        key = create_ec_key()
    else:
        raise MakeCertError(f'Unknown key_type == {key_type}')

    save_key(key, save_to=key_path)

    # TODO load if exists
    subject = subjects[options['subject']]
    cert = create_cert(
        subject=subject,
        key=key,
        issuer_cert=issuer_cert,
        signing_key=signing_key,
        not_valid_after_days=options.get('not_valid_after_days')
    )
    save_cert(cert, save_to=cert_path)

    for next_cert_path_str, next_cert_options in options.get('issue', {}).items():
        next_cert_path = Path(next_cert_path_str)
        cert_from_dict(
            next_cert_path,
            options=next_cert_options,
            subjects=subjects,
            issuer_cert=cert,
            signing_key=key,
        )


def process_hier_file(hier_file_path: Path) -> None:
    print(f'Creating certificates for {hier_file_path} hierarhy...')
    # TODO Implement intermediate certs
    with open(hier_file_path, 'r') as file:
        data = yaml.safe_load(file)

    names = {k: name_from_dict(val) for k, val in data['names'].items()}
    certs: dict[str, x509.Certificate] = {}
    keys: dict[str, KeyType] = {}

    for cert_path_str, cert_dict in data['certs'].items():
        cert_from_dict(Path(cert_path_str), options=cert_dict, subjects=names)
    print(f'Hierarhy {hier_file_path} is done.')


if __name__ == '__main__':
    args = get_args()
    process_hier_file(args.filename)
