#! /usr/bin/env python3

"""
The script is a part of Salt.Box Compose.

Check latest available release tags for images in Salt.Box Compose.

Requires python>=3.7.3 and install_saltbox.py script
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, NewType

from install_saltbox import GitLabRepo

URL = 'https://dev.saltbox.pro'
GROUP = 'saltbox'
IS_PRERELEASE_OK = True

Conf = NewType('Conf', Dict[str, Any])
VarRepoMap = NewType('VarRepoMap', Dict[str, str])
GROUP_URL = 'https://dev.saltbox.pro/saltbox'
# Example: ${IMAGE_REGISTRY}/saltbox-core:${CORE_IMAGE_TAG}
IMAGE_PATTERN = re.compile(r'^\$\{IMAGE_REGISTRY\}\/(?P<path>.*):\$\{(?P<tag_var>.*)\}$')


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


def proc_map(map: VarRepoMap, token: str) -> None:
    for var, url in map.items():
        repo = GitLabRepo(url=url, token=token)
        tag = repo.get_version_tags(allow_pre_releases=IS_PRERELEASE_OK)[-1]
        print(f"{var}='{tag}'")


def main() -> None:
    private_token = os.environ['GITLAB_TOKEN']

    img_repo_map = {}
    for entry in get_image_entries(get_conf()):
        match = IMAGE_PATTERN.match(entry)
        if match:
            path = match.group('path')
            tag_var = match.group('tag_var')
            repo_path = path.split('/')[0]
            img_repo_map[tag_var] = f'{GROUP_URL}/{repo_path}'

    img_repo_map = dict(sorted(img_repo_map.items(), key=lambda pair: pair[0]))
    main_vars = filter_main_compose_vars(list(img_repo_map))
    main_map = VarRepoMap({k: val for k, val in img_repo_map.items() if k in main_vars})
    addons_map = VarRepoMap({k: val for k, val in img_repo_map.items() if k not in main_vars})

    print('Main Salt.Box Compose vars:')
    print('___')
    proc_map(main_map, token=private_token)
    print('')
    print('Salt.Box vars for addons:')
    print('___')
    proc_map(addons_map, token=private_token)

    print('___')
    print('Done')


if __name__ == '__main__':
    main()
