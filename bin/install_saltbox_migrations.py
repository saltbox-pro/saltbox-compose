#! /usr/bin/env python3

# Copyright 2026 Anton Karmanov

"""
The script is a part of Salt.Box Compose.

Salt.Box Migrations is (currently) proprietary subsystem for Salt.Box.
It implements complex processes on clients.

Rather than most Addons the Migrations implemented as a standalone Compose project.

Requires python>=3.7.3

The script depends on some other scripts in `saltbox-compose/bin/`
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import NoReturn

from install_saltbox import RELEASE_REF, TOKEN, TOKEN_NAME, VERSION_TAG_PATTERN, GitLabRepo, cd, print_err, run_cmd

MIN_PYTHON = '3.7.3'
MIGRATIONS_REPO = GitLabRepo(
    url='https://dev.saltbox.pro/saltbox/saltbox-migration-compose/',
    token=TOKEN,
)
UP_CMD = ['docker', 'compose', 'up', '--detach']
CLEANUP_CMD = ['docker', 'compose', 'down', '--volumes', '--remove-orphans']
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
        '--discovery-host',
        type=str,
        required=True,
        help=(
            'IP address (not loopback e.g. 127.0.0.1) or '
            'DNS name (non-local, not from `/etc/hosts`) to connect to Salt.Box'
        ),
    )
    parser.add_argument(
        '--discovery-port',
        type=int,
        default=443,
        help='Port to access Salt.Box instance',
    )
    parser.add_argument(
        '--saltbox-outer-socket',
        type=str,
        required=True,
        help='Usually value of `saltbox-compose/.env` WEB_SERVER_OUTER_SOCKET var',
    )
    parser.add_argument(
        '--discovery-instance-host',
        type=str,
        required=True,
        help='Salt.Box Migrations callback IP address or resolvable for Salt.Box hostname',
    )
    parser.add_argument(
        '--discovery-front-container-name',
        type=str,
        help=(
            'Address for Salt.Box to obtain Migrations Frontend. '
            'By default equals to `--discovery-instance-host` which is OK '
            'for external Salt.Box Migrations instance'
        ),
    )
    parser.add_argument(
        '--rabbitmq-host',
        type=str,
        help=(
            'Adddress to connect to AMPQ dispatcher. '
            'By default equals to `--discovery-host` which is OK for external '
            'Salt.Box Migrations instance'
        ),
    )
    # END OF DOTENV RELATED PARAMS
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help=(
            'Cleanup possibly existing Salt.Box Migration instance '
            'with the same COMPOSE_PROJECT_NAME. '
            'BEWARE OF DATA LOST!'
        ),
    )
    parser.add_argument(
        '--git',
        action='store_true',
        help='Clone Git repo rather than download files (Git required)',
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Do not show downloading progress, CI-friendly',
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=Path(),
        help='Directory to put Migrations Compose',
    )
    parser.add_argument(
        '-u', '--skip-run',
        action='store_true',
        help='Prepare but do not run',
    )
    args = parser.parse_args()
    if (
        args.compose_ref not in KNOWN_REF and
        not VERSION_TAG_PATTERN.match(args.compose_ref)
    ):
        error(f'Unsupported `--compose-ref` value `{args.compose_ref}`')
    if args.discovery_front_container_name is None:
        args.discovery_front_container_name = args.discovery_instance_host
    if args.rabbitmq_host is None:
        args.rabbitmq_host = args.discovery_host
    return args


def _make_secrets(output_dir: Path) -> None:
    bin_dir = Path(__file__).parent.resolve()
    assert_msg = f'Failed to obtain absolute path to scripts dir. Check Python version to be >= {MIN_PYTHON}.'
    assert bin_dir.is_absolute(), assert_msg
    mk_scrts_cmd = [
        str(bin_dir / 'make_secrets.py'),
        '--output-dir', str(output_dir / 'secrets'),
        str(output_dir / 'secrets.json')
    ]
    run_cmd(mk_scrts_cmd)


def main() -> None:
    if TOKEN is None:
        error(f'Missing required `{TOKEN_NAME}` environment variable to install proprietary Migrations subsystem')

    args = get_args()
    output_dir = args.path / 'saltbox-migration-compose'

    ref = MIGRATIONS_REPO.normalize_ref(args.compose_ref)

    override = [
        ('SALTBOX_GATEWAY_IP', args.discovery_host),
        ('DISCOVERY_SERVER_OUTER_SOCKET', args.saltbox_outer_socket),
        ('DISCOVERY_DISCOVERY_URL', f'https://{args.discovery_host}:{args.discovery_port}/api/discovery'),
        ('DISCOVERY_INSTANCE_HOST', args.discovery_instance_host),
        ('DISCOVERY_FRONT_CONTAINER_NAME', args.discovery_front_container_name),
        ('RABBIT_HOST', args.rabbitmq_host),
    ]

    if not VERSION_TAG_PATTERN.match(ref):
        # Supposed ref is a branch
        override = [
            ('FRONTEND_IMAGE_TAG', ref),
            ('BACKEND_IMAGE_TAG', ref),
            *override,
        ]

    output_dir.parent.mkdir(exist_ok=True, parents=True)
    MIGRATIONS_REPO.obtain_ref(
        use_git=args.git,
        ref=ref,
        output_dir=output_dir,
        progress=not args.no_progress,
    )

    _make_secrets(output_dir=output_dir)

    with cd(output_dir):
        dotenv = Path('.env')
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
        if args.cleanup:
            run_cmd(CLEANUP_CMD)
        run_cmd(UP_CMD, skip=args.skip_run)


if __name__ == '__main__':
    main()
