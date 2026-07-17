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
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, NewType

from install_saltbox import VERSION_TAG_PATTERN, GitLabRepo, Version

GITLAB_INSTANCE_URL = 'https://dev.saltbox.pro'
GROUP = 'saltbox'
IS_PRERELEASE_OK = True
DEFAULT_CMD = 'list'
UPDATE_AND_RUN_LIST_SEP = ':,'

Conf = NewType('Conf', Dict[str, Any])
# Example: ${IMAGE_REGISTRY}/saltbox-core:${CORE_IMAGE_TAG}
IMAGE_PATTERN = re.compile(r'^\$\{IMAGE_REGISTRY\}\/(?P<path>.*):\$\{(?P<tag_var>.*)\}$')

BIN_DIR = Path(__file__).parent.resolve()
DOTENV_TOOL_PATH = BIN_DIR / 'dotenv_tool.sh'


@dataclass
class ImageEntry:
    registry: str
    path: str
    tag: str
    tag_var: str

    @property
    def location(self) -> str:
        return f'{self.registry}/{self.path}'

    @property
    def repo_path(self) -> str:
        grp = self.registry.split('/')[-1]
        proj = self.path.split('/')[0]
        return f'{grp}/{proj}'

    def __str__(self) -> str:
        return f'{self.location}:{self.tag}'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='image_tags',
        description='Help to set release tags for Salt.Box images')
    parser.add_argument(
        'command',
        nargs='?',
        choices=['list', 'check'],
        default=DEFAULT_CMD,
        help=f"Command to run, '{DEFAULT_CMD}' by default")
    parser.add_argument(
        '--only-addons',
        action='store_true',
        help='Ignore main Salt.Box compose images'
    )
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
    result = set()
    for val in conf['services'].values():
        image = val.get('image')
        if image is None:
            continue
        result.add(image)
    return list(result)


def filter_main_compose_images(
    images: List[ImageEntry], exclude: bool = False
) -> List[ImageEntry]:
    with open('base.env') as dotenv_f:
        dotenv = dotenv_f.read()
    return [i for i in images if exclude != (i.tag_var in dotenv)]


@lru_cache(maxsize=None)
def get_repo_registry(url: str, token: str) -> Dict:
    repo = GitLabRepo(url=url, token=token)
    return repo.get_registry_repositories(tags=True)


def get_latest_tag(image: ImageEntry, token: str) -> str:
    repo_url = f'{GITLAB_INSTANCE_URL}/{image.repo_path}'
    data = get_repo_registry(url=repo_url, token=token)
    for registry_entry in data:
        if registry_entry['location'] == image.location:
            tags = [tag_entry['name'] for tag_entry in registry_entry['tags']]
            break
    else:
        dosa = f'Failed to find tags for `{image.location}` in `{image.registry}`'
        raise RuntimeError(dosa)

    release_tags = list(filter(lambda x: VERSION_TAG_PATTERN.match(x), tags))
    ver_objs = [Version.from_str(v.lstrip('v')) for v in release_tags]
    versions = [f'v{ver}' for ver in sorted(ver_objs)]
    return versions[-1]


def cmd_list(images: List[ImageEntry], token=str) -> None:
    def proc_map(images: List[ImageEntry], token: str) -> None:
        listed = set()
        for img in images:
            if img.tag_var in listed:
                continue
            latest_tag = get_latest_tag(image=img, token=token)
            print(f"{img.tag_var}='{latest_tag}'")
            listed.add(img.tag_var)

    main_images = filter_main_compose_images(images)
    addons_images = [i for i in images if i not in main_images]

    if main_images:
        print('Main Salt.Box Compose vars:')
        print('___')
        proc_map(main_images, token=token)
        print('')
    print('Salt.Box vars for addons:')
    print('___')
    proc_map(addons_images, token=token)

    print('___')
    print('Done')


def get_dotenvs() -> List[str]:
    cmd = ['bash', str(DOTENV_TOOL_PATH), 'env-files']
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    val = proc.stdout
    return val.splitlines()


def get_dotenv_var(name: str) -> str:
    cmd = ['bash', str(DOTENV_TOOL_PATH), 'get', name]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    val = proc.stdout
    if val.endswith('\n'):
        val = val[:-1]
    return val


def cmd_check(images: List[ImageEntry], token: str) -> None:
    dosa_counter = 0
    dotenvs = get_dotenvs()
    print('Checking variables in following sources:')
    for de in dotenvs:
        print(f'  - {de}')
    print()
    for image in {i.tag_var: i for i in images}.values():  # Uniq by ImageEntry.tag_var
        latest_tag = get_latest_tag(image=image, token=token)
        if image.tag != latest_tag:
            dosa_counter += 1
            dosa = f"{image.tag_var}='{image.tag}' does not match tag '{latest_tag}'"
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

    registry = get_dotenv_var('IMAGE_REGISTRY')
    images: List[ImageEntry] = []
    for entry in get_image_entries(get_conf()):
        match = IMAGE_PATTERN.match(entry)
        if match:
            path = match.group('path')
            tag_var = match.group('tag_var')
            tag = get_dotenv_var(name=tag_var)
            images.append(
                ImageEntry(registry=registry, path=path, tag=tag, tag_var=tag_var)
            )

    images.sort(key=lambda i: i.tag_var)
    if args.only_addons:
        images = filter_main_compose_images(images, exclude=True)

    if args.command == 'list':
        cmd_list(images, token=private_token)
    if args.command == 'check':
        cmd_check(images, token=private_token)


if __name__ == '__main__':
    main()
