#! /usr/bin/env python3

# Copyright 2026 Anton Karmanov

"""
The script is a part of Salt.Box Compose.

Salt.Box Migrations is (currently) proprietary subsystem for Salt.Box.
It implements complex processes on clients.

Rather than most Addons the Migrations implemented as a standalone Compose project.

Requires python>=3.7.3
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import NoReturn

from install_saltbox import RELEASE_REF, TOKEN, TOKEN_NAME, VERSION_TAG_PATTERN, GitLabRepo, cd, print_err, run_cmd

MIGRATIONS_REPO = GitLabRepo(
    url='https://dev.saltbox.pro/saltbox/saltbox-migration-compose/',
    token=TOKEN,
)
UP_CMD = ['docker', 'compose', 'up', '--detach']
MONGO_SECRET_VAR = 'MONGO_ADMIN_PASSWORD'
MONGO_SECRET = os.environ.get(MONGO_SECRET_VAR)
KNOWN_REF = ['dev', 'master', RELEASE_REF]


def error(msg: str) -> NoReturn:
    print_err('', msg, '')
    sys.exit(1)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run Salt.Box Migrations',
        epilog=f'Environment variables `{TOKEN_NAME}` and are obligatory.',
    )
    parser.add_argument(
        'OVERRIDE',
        nargs='*',
        type=str,
        help='Extra values to include into dotenv in form of NAME=\'VAL\'',
    )
    parser.add_argument(
        '--git',
        action='store_true',
        help='Clone Git repo rather than download files (Git required)',
    )
    parser.add_argument(
        '--migrations-host',
        type=str,
        required=True,
        help=(
            'IP address (not loopback e.g. 127.0.0.1) or '
            'DNS name (non-local, not from `/etc/hosts`) on which '
            'Salt.Box Migrations will be served. Usually equals '
            '`--saltbox-address` when served on the same host.'
        ),
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=Path(),
        help='Directory to put Migrations Compose',
    )
    parser.add_argument(
        '--compose-ref',
        type=str,
        default=RELEASE_REF,
        help=(
            'Migrations Compose Git reference to obtain, '
            f'`{RELEASE_REF}` to search fo latest release tag, '
            '`dev` and `master` for main dev-branches. '
            'Version tag `v*.*.*` for a specific release (MAY be unmaintained!).'
            f'`{RELEASE_REF}` by default.'
        )
    )
    parser.add_argument(
        '--saltbox-address',
        type=str,
        required=True,
        help=(
            'IP address (not loopback e.g. 127.0.0.1) or '
            'DNS name (non-local, not from `/etc/hosts`) to connect to Salt.Box'
        ),
    )
    parser.add_argument(
        '--saltbox-outer-socket',
        type=str,
        required=True,
        help='Usually value of `saltbox-compose/.env` WEB_SERVER_OUTER_SOCKET var',
    )
    parser.add_argument(
        '--saltbox-port',
        type=int,
        default=443,
        help='Port to access Salt.Box instance',
    )
    args = parser.parse_args()
    if (
        args.compose_ref not in KNOWN_REF and
        not VERSION_TAG_PATTERN.match(args.compose_ref)
    ):
        error(f'Unsupported `--compose-ref` value `{args.compose_ref}`')
    return args

def main() -> None:
    args = get_args()
    output_dir = args.path / './saltbox-migration-compose'
    mongo_secret_path = Path('secrets/mongo_admin_password')

    ref = MIGRATIONS_REPO.normalize_ref(args.compose_ref)

    override = [
        ('MODULE_HOST_IP', args.migrations_host),
        ('SALTBOX_GATEWAY_IP', args.saltbox_address),
        ('DISCOVERY_SERVER_OUTER_SOCKET', args.saltbox_outer_socket),
        ('DISCOVERY_DISCOVERY_URL', f'https://{args.saltbox_address}:{args.saltbox_port}/api/discovery'),
        ('DISCOVERY_INSTANCE_HOST', args.saltbox_address),
        ('DISCOVERY_FRONT_CONTAINER_NAME', args.saltbox_address),
        ('RABBIT_HOST', args.saltbox_address),
    ]

    if not VERSION_TAG_PATTERN.match(ref):
        # Supposed ref is a branch
        override = [
            ('FRONTEND_IMAGE_TAG', ref),
            ('BACKEND_IMAGE_TAG', ref),
            *override,
        ]


    for name, val in [(TOKEN_NAME, TOKEN), (MONGO_SECRET_VAR, MONGO_SECRET)]:
        if val is None:
            error( f'Missing required `{name}` environment variable to install proprietary Migrations subsystem')
    assert MONGO_SECRET is not None

    output_dir.parent.mkdir(exist_ok=True, parents=True)
    MIGRATIONS_REPO.obtain_ref(use_git=args.git, ref=ref, output_dir=output_dir)

    with cd(output_dir):
        dotenv = Path('.env')
        mongo_secret_path.parent.mkdir(parents=True, exist_ok=True)
        with mongo_secret_path.open('a') as file:
            file.write(MONGO_SECRET)

        shutil.copy('example.env', dotenv)

        with dotenv.open('a') as file:
            file.write('\n')
            file.write('#' * 80 + '\n')
            file.write('## OVERRIDED VALUES\n')
            file.write('#' * 80 + '\n')
            for key, val in override:
                file.write(f"{key}='{val}'\n")
            for val in args.OVERRIDE:
                file.write(f'{val}\n')
        run_cmd(UP_CMD)


if __name__ == '__main__':
    main()
