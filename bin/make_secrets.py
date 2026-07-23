#! /usr/bin/env python3

"""
Create password files by simple JSON config files. Config format is:
    [
      {
        "name": "NAME_OF_SECRET_FILE",
        "length": PASSWORD_LENGTH
      },
    ]
"""

# Requires python>=3.7.3

import argparse
import json
import os
import secrets
import shutil
import string
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SECRET_ALPHABET = string.ascii_letters + string.digits
UMASK = 0o077


@dataclass
class Secret:
    name: str
    length: int


def rm(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def path_of_secret(secrets_dir: Path, secret_name: str) -> Path:
    return secrets_dir / secret_name


def random(length, alphabet=SECRET_ALPHABET) -> str:
    return ''.join(secrets.choice(alphabet) for i in range(length))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='make_secrets',
        description='Generate passwords for Salt.Box installation',)
    parser.add_argument(
        'file',
        nargs='*',
        default=['secrets.json'],
        help='Files with',)
    parser.add_argument(
        '--explicit',
        action='append',
        default=[],
        help=(
            'Set a secret value explicitly in form of `NAME=VALUE`. '
            'Can be specified multiple times.'
        ),)
    default_output_dir = get_default_secrets_dir()
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        default=default_output_dir,
        help=f'Alternative location for secrets, by default `{default_output_dir}`'
    )
    parser.add_argument(
        '--prune',
        help='Delete files, which are not related to specified secrets',
        action='store_true',)
    parser.add_argument(
        '-w',
        '--overwrite',
        help='Overwrite existing passwords',
        action='store_true',)
    return parser.parse_args()


def make_secret(
    path: Path,
    secret_length: int,
    explicit_value: Optional[str] = None,
    overwrite=False
) -> None:
    is_existing = path.exists()
    if is_existing and not overwrite:
        print(f'Skip existing `{path}`', file=sys.stderr)
        return
    with open(path, 'w') as f:
        if is_existing:
            print(f'Overwriting `{path}`')
        else:
            print(f'Creating `{path}`')
        val = random(length=secret_length) if explicit_value is None else explicit_value
        f.write(val)


def prune(secrets: List[Secret], secrets_dir: Path) -> None:
    good_files = {path_of_secret(secrets_dir, sec.name) for sec in secrets}
    for path in secrets_dir.iterdir():
        if path not in good_files and path and not path.name.startswith('.'):
            print(f'Delete {path}')
            rm(path)


def validate_conf(data: Any) -> List[Secret]:
    if not isinstance(data, list):
        raise ValueError('Secrets config must be enumerated in array')

    result = []

    for i in data:
        if not isinstance(i, dict):
            raise ValueError('Secret must be declared as an object')
        for field, f_type in {'name': str, 'length': int}.items():
            if field not in i:
                msg = f'Missing "{field}" in {i}'
                raise ValueError(msg)
            if not isinstance(i[field], f_type):
                msg = f'"{field}" must be of type {f_type} in {i}'
                raise ValueError(msg)
        result.append(Secret(**i))

    return result


def parse_configs(paths: List[Union[str, Path]]) -> List[Secret]:
    result = []
    for path in paths:
        print(f'Reading "{path}"')
        with Path(path).open('r') as file:
            result.extend(validate_conf(json.load(file)))
    secrets = [i.name for i in result]
    dups = [item for item, cnt in Counter(secrets).items() if cnt > 1]
    if dups:
        msg = f'Duplicated secrets found in configs: {", ".join(dups)}'
        raise ValueError(msg)
    return result


def get_default_secrets_dir() -> Path:
    base_dir = Path(__file__).parent.parent.resolve()
    secrets_dir = base_dir / 'secrets'
    assert secrets_dir.is_absolute(), 'Expected to have absolute path to secrets dir'
    return secrets_dir


def ensure_secrets_dir(secrets_dir: Path) -> None:
    if not secrets_dir.exists():
        secrets_dir.mkdir(parents=True)
    elif not secrets_dir.is_dir():
        dosa = f'Output path exists and is not a directory: "{secrets_dir}"'
        raise OSError(dosa)


def parse_explicits(explicits: List[str]) -> Dict[str, str]:
    result = {}
    for x in explicits:
        spl = x.split('=', maxsplit=1)
        if len(spl) != 2 or not spl[1]:
            raise ValueError(f'Incorrect explicit secret arg: `{x}`')
        result[spl[0]] = spl[1]
    return result


def main() -> None:
    args = parse_args()
    try:
        explicits = parse_explicits(args.explicit)
    except (ValueError) as err:
        print(f'ERROR {err}', file=sys.stderr)
        sys.exit(1)

    os.umask(UMASK)

    secrets_dir = args.output_dir
    ensure_secrets_dir(secrets_dir)
    print(f'Secrets dir is "{secrets_dir}"')

    try:
        secrets = parse_configs(args.file)
    except (ValueError, OSError) as err:
        print(f'ERROR {err}', file=sys.stderr)
        sys.exit(1)
    print(f'Found {len(secrets)} secret entries in {len(args.file)} config files')

    for x in explicits:
        if x not in {s.name for s in secrets}:
            dosa = f'Explicit secret `{x}` is given, but no such secret in configs'
            print(f'ERROR {dosa}', file=sys.stderr)
            sys.exit(1)

    if args.prune:
        prune(secrets=secrets, secrets_dir=secrets_dir)
    for sec in secrets:
        path = path_of_secret(secrets_dir, sec.name)
        explicit_val = explicits.get(sec.name)
        try:
            make_secret(
                path=path, secret_length=sec.length,
                explicit_value=explicit_val, overwrite=args.overwrite)
        except OSError as err:
            print(f'ERROR {err}', file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
