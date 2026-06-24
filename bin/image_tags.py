#! /usr/bin/env python3

"""
The script is a part of Salt.Box Compose.

Check latest available release tags for images in Salt.Box Compose.

Requires python>=3.7.3 and install_saltbox.py script
"""

import argparse
import json
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, NewType

from install_saltbox import GitLabRepo, get_dotenv_var

URL = 'https://dev.saltbox.pro'
GROUP = 'saltbox'
IS_PRERELEASE_OK = True

Conf = NewType('Conf', Dict[str, Any])
VarRepoMap = NewType('VarRepoMap', Dict[str, str])
GROUP_URL = 'https://dev.saltbox.pro/saltbox'
# Example: ${IMAGE_REGISTRY}/saltbox-core:${CORE_IMAGE_TAG}
IMAGE_PATTERN = re.compile(r'^\$\{IMAGE_REGISTRY\}\/(?P<path>.*):\$\{(?P<tag_var>.*)\}$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='image_tags',
        description='Help to set release tags for Salt.Box images',)
    parser.add_argument(
        'command',
        nargs='?',
        choices=['list', 'check'],
        default='list',
        help="Command to run. 'list' to show latest tags, 'check' to validate current tags",)
    return parser.parse_args()


def get_conf() -> Conf:
    bin_dir = Path(__file__).resolve().parent
    bin_path = bin_dir / 'sb-compose.sh'
    cmd = [str(bin_path), 'config', '--no-interpolate', '--format=json']
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        cmd_str = ' '.join(cmd)
        stderr = err.stderr.decode()
        dosa = f'Command failed: {cmd_str}, sterr:\n{stderr}'
        raise RuntimeError(dosa)
    return json.loads(result.stdout)


def get_image_entries(conf: Conf) -> List[str]:
    result = []
    for k, val in conf['services'].items():
        image = val.get('image')
        if image is None:
            continue
        result.append(image)
    return result


def filter_main_compose_vars(vars: List[str]) -> List[str]:
    with open('base.env') as dotenv_f:
        dotenv = dotenv_f.read()
    return [v for v in vars if v in dotenv]


@lru_cache(maxsize=None)
def get_latest_tag(url: str, token: str) -> str:
    repo = GitLabRepo(url=url, token=token)
    tag = repo.get_version_tags(allow_pre_releases=IS_PRERELEASE_OK)[-1]
    return tag


def proc_map(map: VarRepoMap, token: str) -> None:
    for var, url in map.items():
        tag = get_latest_tag(url=url, token=token)
        print(f"{var}='{tag}'")


def cmd_list(map: Dict[str, str], token=str) -> None:
    main_vars = filter_main_compose_vars(list(map))
    main_map = VarRepoMap({k: val for k, val in map.items() if k in main_vars})
    addons_map = VarRepoMap({k: val for k, val in map.items() if k not in main_vars})

    print('Main Salt.Box Compose vars:')
    print('___')
    proc_map(main_map, token=token)
    print('')
    print('Salt.Box vars for addons:')
    print('___')
    proc_map(addons_map, token=token)

    print('___')
    print('Done')


def get_extra_envs() -> List[str]:
    extra = get_dotenv_var('_UPDATE_AND_RUN_EXTRA_ENV_FILES', ['override.env'])
    return extra.split(',')


def cmd_check(map: Dict[str, str], token: str) -> None:
    dosa_counter = 0
    dotenvs = ['base.env', *get_extra_envs()]
    print('Checking variables in following sources:')
    for de in dotenvs:
        print(f'  - {de}')
    print()
    for var, url in map.items():
        val = get_dotenv_var(var, dotenvs=dotenvs)
        tag = 'dev'
        tag = get_latest_tag(url, token=token)
        if not val:
            dosa = f'No value for {var}, missing module .env?'
            print(dosa, file=sys.stderr)
        elif val != tag:
            dosa_counter += 1
            dosa = f"{var}='{val}' does not match tag '{tag}'"
            print(dosa, file=sys.stderr)
    print('___')
    if dosa_counter:
        print(f'Improper variables found: {dosa_counter}!', file=sys.stderr)
        sys.exit(1)
    print('Done')


def main() -> None:
    args = parse_args()
    private_token = os.environ['GITLAB_TOKEN']

    print('\n', '  ', '#' * 67, sep='')
    print("  # Be sure to have all required modules enabled in 'override.env'! #")
    print('  ', '#' * 67, '\n', sep='')

    img_repo_map = {}
    for entry in get_image_entries(get_conf()):
        match = IMAGE_PATTERN.match(entry)
        if match:
            path = match.group('path')
            tag_var = match.group('tag_var')
            repo_path = path.split('/')[0]
            img_repo_map[tag_var] = f'{GROUP_URL}/{repo_path}'

    img_repo_map = dict(sorted(img_repo_map.items(), key=lambda pair: pair[0]))

    if args.command == 'list':
        cmd_check(map=img_repo_map, token=private_token)
    if args.command == 'check':
        cmd_check(map=img_repo_map, token=private_token)


if __name__ == '__main__':
    main()
