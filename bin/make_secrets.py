#! /usr/bin/env python3

import argparse
import string
import secrets
import shutil
import sys

from pathlib import Path

SECRETS = {
    'keycloak_admin_password': 16,
    'keycloak_client_saltbox_core_password': 16,
    'keycloak_client_grafana_password': 16,
    'keycloak_database_password': 16,
    'mongo_admin_password': 16,
    'redis_salt_ca_private_key_password': 16,
    'redis_salt_password': 16,
    'redis_salt_private_key_password': 16,
    'redis_taskiq_password': 16,
    'saltbox_admin_password': 12,
    'saltbox_user_password': 12,
    'sshfs_user_master_password': 12,
    'sshfs_user_saltbox_password': 12,
    'mongo_keyfile': 16,
    # TODO 'mongo_keyfile': 512,
}

SECRET_ALPHABET = string.ascii_letters + string.digits


def rm(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def path_of_secret(secrets_dir: Path, secret_name: str) -> Path:
    return secrets_dir / secret_name


def random(length, alphabet=SECRET_ALPHABET) -> str:
    return ''.join(secrets.choice(alphabet) for i in range(length))


def make_secret(path: Path, secret_length: int, overwrite=False) -> None:
    is_existing = path.exists()
    if is_existing and not overwrite:
        print(f'Skip existing {path}', file=sys.stderr)
        return
    with open(path, 'w') as f:
        if is_existing:
            print(f'Overwriting {path}')
        else:
            print(f'Creating {path}')
        f.write(random(length=secret_length))


def main(secrets_dir: Path, overwrite: bool) -> None:
    for sec, length in SECRETS.items():
        path = path_of_secret(secrets_dir, sec)
        make_secret(path=path, secret_length=length, overwrite=overwrite)


def prune(secrets_dir: Path) -> None:
    good_files = {path_of_secret(secrets_dir, sec) for sec in SECRETS}
    for path in secrets_dir.iterdir():
        if path not in good_files and path and not path.name.startswith('.'):
            print(f'Delete {path}')
            rm(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='make_secrets',
        description='Generate passwords for Salt.Box installation',)
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
    secrets_dir = Path(__file__).parent.parent / 'secrets'
    assert secrets_dir.is_absolute(), 'Expected to have absolute path to secrets dir'
    if args.prune:
        prune(secrets_dir)
    main(secrets_dir=secrets_dir, overwrite=args.overwrite)
