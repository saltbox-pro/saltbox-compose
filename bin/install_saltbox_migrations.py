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
from pathlib import Path
from typing import List

from install_saltbox import (
    RELEASE_REF,
    TOKEN,
    TOKEN_NAME,
    VERSION_TAG_PATTERN,
    Config,
    GitLabRepo,
    InstallerError,
    cd,
    check_repo_compability_level,
    print_installer_error_and_exit,
    run_cmd,
)

MIN_PYTHON = '3.7.3'
MIGRATIONS_REPO = GitLabRepo(
    url='https://dev.saltbox.pro/saltbox/saltbox-migration-compose/',
    token=TOKEN,
)
UP_CMD = ['docker', 'compose', 'up', '--detach']
DOWN_CMD = ['docker', 'compose', 'down']
CLEANUP_CMD = ['docker', 'compose', 'down', '--volumes', '--remove-orphans']
MIGRATIONS_COMPOSE_REQUIRED_COMPATIBILITY_LEVEL = 1


def validate_args(args: argparse.Namespace) -> argparse.Namespace:
    if (
        args.compose_ref not in Config.SUPPORTED_REFS and
        not VERSION_TAG_PATTERN.match(args.compose_ref)
    ):
        raise InstallerError(f'Unsupported `--compose-ref` value `{args.compose_ref}`')

    external_triade = ['saltbox_host', 'saltbox_port', 'migrations_host']
    external_triade_vals = [getattr(args, i) for i in external_triade]
    substr = ', '.join(f'`--{i.replace("_", "-")}`' for i in external_triade)
    if not args.internal and None in external_triade_vals:
        raise InstallerError(f'Flags {substr} are all required without `--internal` flag')
    if args.internal and any([i is not None for i in external_triade_vals]):
        raise InstallerError(f'Flags {substr} are ignored with `--internal` flag')

    return args


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
        '--saltbox-outer-socket',
        type=str,
        required=True,
        help='Usually value of `saltbox-compose/.env` WEB_SERVER_OUTER_SOCKET var',
    )
    parser.add_argument(
        '--internal',
        action='store_true',
        help=(
            'If current host has Salt.Box instance, shared Docker network will '
            'be used to connect the Salt.Box Migrations.'
        )
    )
    parser.add_argument(
        '--saltbox-host',
        type=str,
        help=(
            'IP address (not loopback e.g. 127.0.0.1) or '
            'DNS name (non-local, not from `/etc/hosts`) to connect to Salt.Box. '
            'The host must be accessible for Migrations containers. Real IP addres '
            'of a network interface is a good choice.'
        ),
    )
    parser.add_argument(
        '--saltbox-port',
        type=int,
        help=(
            'Port to access Salt.Box instance. Usually matches '
            '`--saltbox-outer-socket` port, but may differ if '
            'the whole installation is behind an outer reverse-proxy.'
        )
    )
    parser.add_argument(
        '--migrations-host',
        type=str,
        help=(
            'Salt.Box Migrations callback IP address or hostname which is '
            'resolvable and accessible for Salt.Box. May match `--saltbox-host` '
            'for a same-host installation.'
        )
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
    return validate_args(parser.parse_args())


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


def make_override(args: argparse.Namespace) -> List[str]:
    if args.internal:
        pairs = [
            ('EXPOSE_HOST', '127.0.0.1'),
            ('NETWORK_NAME', 'saltbox_default'),
            ('NETWORK_EXTERNAL', 'true'),
            ('RABBITMQ_HOST', 'rabbitmq'),
            ('DISCOVERY_IS_EXTERNAL', 'False'),
            ('DISCOVERY_SERVER_OUTER_SOCKET', args.saltbox_outer_socket),
            ('DISCOVERY_DISCOVERY_URL', 'http://saltbox-gateway:8001/api/discovery'),
            ('DISCOVERY_FRONT_CONTAINER_NAME', 'migrations-frontend'),
            ('DISCOVERY_FRONT_CONTAINER_PORT', '80'),
            ('DISCOVERY_INSTANCE_HOST', 'migrations-backend'),
        ]
    else:
        pairs = [
            ('RABBITMQ_HOST', args.saltbox_host),
            ('DISCOVERY_SERVER_OUTER_SOCKET', args.saltbox_outer_socket),
            ('DISCOVERY_DISCOVERY_URL', f'https://{args.saltbox_host}:{args.saltbox_port}/api/discovery'),
            ('DISCOVERY_INSTANCE_HOST', args.migrations_host),
            ('DISCOVERY_FRONT_CONTAINER_NAME', args.migrations_host),
        ]
    return [f"{key}='{val}'" for key, val in pairs]


def main() -> None:
    if TOKEN is None:
        dosa = f'Missing required `{TOKEN_NAME}` environment variable to install proprietary Migrations subsystem'
        raise InstallerError(dosa)

    args = get_args()
    output_dir = args.path / 'saltbox-migration-compose'

    ref = MIGRATIONS_REPO.normalize_ref(args.compose_ref)

    override = make_override(args)
    override.extend(args.OVERRIDE)

    if not VERSION_TAG_PATTERN.match(ref):
        # Supposed ref is a branch
        override = [
            f"FRONTEND_IMAGE_TAG='{ref}'",
            f"BACKEND_IMAGE_TAG='{ref}'",
            *override,
        ]

    output_dir.parent.mkdir(exist_ok=True, parents=True)
    MIGRATIONS_REPO.obtain_ref(
        use_git=args.git,
        ref=ref,
        output_dir=output_dir,
        progress=not args.no_progress,
    )
    check_repo_compability_level(
        repo_path=output_dir,
        required_level=MIGRATIONS_COMPOSE_REQUIRED_COMPATIBILITY_LEVEL
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
            for line in override:
                file.write(line + '\n')
        if args.cleanup:
            run_cmd(CLEANUP_CMD)
        else:
            run_cmd(DOWN_CMD)
        run_cmd(UP_CMD, skip=args.skip_run)


if __name__ == '__main__':
    try:
        main()
    except InstallerError as papa:
        print_installer_error_and_exit(papa)
