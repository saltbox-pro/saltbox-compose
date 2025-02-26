#! /bin/env python3

import argparse
import string
import secrets
import shutil
import sys

from pathlib import Path

SECRETS = {
    'keycloak_admin_password': 16,
    'keycloak_client_salt_box_core_password': 16,
    'keycloak_database_password': 16,
    'keycloak_user_password': 12,
    'mongo_admin_password': 16,
    'redis_celery_password': 16,
    'redis_salt_ca_private_key_password': 16,
    'redis_salt_password': 16,
    'redis_salt_private_key_password': 16,
}


def rm(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


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


def prune(secrets_dir: Path) -> None:
    good_files = {secrets_dir / sec for sec in SECRETS}
    for path in secrets_dir.iterdir():
        if path not in good_files and path and not path.name.startswith('.'):
            print(f'Delete {path}')
            rm(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='make_secrets',
        description='Generate passwords for salt.box installation',)
    parser.add_argument(
        '-w',
        '--overwrite',
        help='Overwrite existing passwords',
        action='store_true',)
    parser.add_argument(
        '--prune',
        help='Delete files, which are not related to specified secrets',
        action='store_true',)
    args = parser.parse_args()
    secrets_dir = Path(__file__).parent / 'secrets'
    if args.prune:
        prune(secrets_dir)
    main(secrets_dir=secrets_dir, overwrite=args.overwrite)
