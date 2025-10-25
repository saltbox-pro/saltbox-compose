#! /usr/bin/env python3

import argparse
import json
import secrets
import shutil
import string
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SECRET_ALPHABET = string.ascii_letters + string.digits


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


def prune(secrets: list[Secret], secrets_dir: Path) -> None:
    good_files = {path_of_secret(secrets_dir, sec.name) for sec in secrets}
    for path in secrets_dir.iterdir():
        if path not in good_files and path and not path.name.startswith('.'):
            print(f'Delete {path}')
            rm(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='make_secrets',
        description='Generate passwords for Salt.Box installation',)
    parser.add_argument(
        'file',
        nargs='*',
        default=['secrets.json'],
        help='Files with',
    )
    parser.add_argument(
        '-w',
        '--overwrite',
        help='Overwrite existing passwords',
        action='store_true',)
    parser.add_argument(
        '--prune',
        help='Delete files, which are not related to specified secrets',
        action='store_true',)
    return parser.parse_args()


def validate_conf(data: Any) -> list[Secret]:
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


def parse_configs(paths: list[str | Path]) -> list[Secret]:
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


def main() -> None:
    args = parse_args()
    secrets_dir = Path(__file__).parent.parent / 'secrets'
    assert secrets_dir.is_absolute(), 'Expected to have absolute path to secrets dir'
    try:
        secrets = parse_configs(args.file)
    except (ValueError, OSError) as err:
        print(f'ERROR {err}', file=sys.stderr)
        sys.exit(1)
    print(f'Found {len(secrets)} secret entries in {len(args.file)} config files')
    if args.prune:
        prune(secrets=secrets, secrets_dir=secrets_dir)
    for sec in secrets:
        path = path_of_secret(secrets_dir, sec.name)
        make_secret(path=path, secret_length=sec.length, overwrite=args.overwrite)


if __name__ == '__main__':
    main()
