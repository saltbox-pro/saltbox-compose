#! /bin/env python3

import argparse
import string
import secrets
import sys

from pathlib import Path

SECRETS = {
    'keycloak_admin_password': 16,
    'keycloak_database_password': 16,
    'keycloak_client_fastms_core_password': 16,
    'mongo_admin_password': 16,
    'salt_api_password': 32,
    'redis_salt_password': 16,
    'redis_salt_ca_private_key_password': 16,
    'redis_salt_private_key_password': 16,
}


def make_secret(length=16, alphabet=string.ascii_letters + string.digits) -> str:
    return ''.join(secrets.choice(alphabet) for i in range(length))


def write_file(path: Path, secret: str, overwrite=False) -> None:
    is_existing = path.exists()
    if is_existing and not overwrite:
        print(f'Skip existing {path}', file=sys.stderr)
        return
    with open(path, 'w') as f:
        if is_existing:
            print(f'Overwriting {path}')
        else:
            print(f'Creating {path}')
        f.write(make_secret())


def main(secrets_dir: Path, overwrite: bool) -> None:
    for sec, length in SECRETS.items():
        path = secrets_dir / sec
        secret = make_secret(length=length)
        write_file(path=path, secret=secret, overwrite=overwrite)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='make_secrets',
        description='Generate passwords for FastMS installation',)
    parser.add_argument(
        '-w',
        '--overwrite',
        help='Overwrite existing passwords',
        action='store_true',)
    args = parser.parse_args()
    secrets_dir = Path(__file__).parent / 'secrets'
    main(secrets_dir=secrets_dir, overwrite=args.overwrite)
