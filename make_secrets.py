#!/bin/env python3

import argparse
import string
import secrets
import sys

from pathlib import Path

SECRETS = (
    'keycloak_admin_password',
    'keycloak_database_password',
)


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
    for sec in SECRETS:
        path = secrets_dir / sec
        write_file(path=path, secret=make_secret(), overwrite=overwrite)


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
