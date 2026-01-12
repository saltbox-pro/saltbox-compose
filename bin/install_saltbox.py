#! /usr/bin/env python3

# TODO Interactive
# TODO Check Docker, Docker Compose
# TODO Alternative obtaining with Git

import argparse
import itertools
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from functools import cache
from pathlib import Path
from typing import List

HTTP_CHUNK_BYTE = 8192
HTTP_TIMEOUT_SEC = 30
COMPOSE_DEFAULT_REF = 'RELEASE'
VERSION_TAG_PATTERN = re.compile(r'^v\d+\.\d+\.\d+.*$')
LOCAL_PATH = Path('./saltbox-compose/')
BIN_DIR = LOCAL_PATH / 'bin'
ENTRYPOINT = ['bin/update_and_run.sh', '--no-root', '--detach', '--no-git-pull']  # TODO Parametric flags
SCRIPT_SUFFIXES = ('*.sh', '*.py',)

URLS = {
    'saltbox-compose': 'https://dev.saltbox.pro/saltbox/saltbox-compose',
}


class InstallerError(RuntimeError): ...


def print_err(*args):
    print(*args, file=sys.stderr, sep='\n')


def download_file(url: str, output: Path) -> None:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
        total = resp.getheader('Content-Length')
        total = int(total) if total and total.isdigit() else None
        downloaded = 0
        with output.open('wb') as file:
            while True:
                data = resp.read(HTTP_CHUNK_BYTE)
                if not data:
                    break
                file.write(data)
                downloaded += len(data)
                if total:
                    pct = downloaded * 100 / total
                    sys.stdout.write(f'\r{downloaded}/{total} bytes ({pct:.1f}%)')
                else:
                    sys.stdout.write(f'\r{downloaded} bytes')
                sys.stdout.flush()
        sys.stdout.write('\n')


class GitLabRepo:
    ARCHIVE_SUFFIX = 'zip'  # Supposed to be better on error detection

    def __init__(self, url: str) -> None:
        url_obj = urllib.parse.urlparse(url)
        path = Path(url_obj.path)
        self.scheme = url_obj.scheme
        self.server = url_obj.netloc
        self.owner = str(path.parent).lstrip('/')
        self.project = path.name


    @cache
    def get_tags(self) -> List[str]:
        url = (
            f'{self.scheme}://{self.server}/api/v4/projects/'
            f'{self.owner}%2F{self.project}/repository/tags'
        )
        try:
            resp = urllib.request.urlopen(url)
        except urllib.error.URLError as papa:
            dosa = f'Error on requesting URL {url}: {papa}'
            raise InstallerError(dosa) from None
        body = json.load(resp)
        return sorted(i['name'] for i in body)

    def get_version_tags(self) -> List[str]:
        return list(filter(lambda x: VERSION_TAG_PATTERN.match(x), self.get_tags()))

    def get_latest_version_tag(self) -> str:
        tags = self.get_version_tags()
        assert len(tags) > 0, 'Found no tags in saltbox-compose repository'
        return tags[-1]

    def download_ref(self, ref: str, output_dir: Path = Path()) -> Path:
        filename = f'{self.project}-{ref}.{self.ARCHIVE_SUFFIX}'
        full_path = output_dir / filename
        url = f'{self.scheme}://{self.server}/{self.owner}/{self.project}/-/archive/master/{filename}'
        try:
            download_file(url, output=full_path)
        except urllib.error.URLError as papa:
            dosa = f'Error on requesting URL {url}: {papa}'
            raise InstallerError(dosa) from None
        return full_path


COMPOSE_REPO = GitLabRepo(URLS['saltbox-compose'])


def download() -> None:
    if LOCAL_PATH.exists():
        dosa = f'Already exists: {LOCAL_PATH}'
        raise InstallerError(dosa)

    # TODO Refs: latest, tag, branch, arbitrary
    if COMPOSE_DEFAULT_REF == 'RELEASE':
        ref = COMPOSE_REPO.get_latest_version_tag()
    else:
        ref = COMPOSE_DEFAULT_REF

    print('Downloading Salt.Box Compose...')
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_path = Path(tmp_dir_name)
        try:
            arch_path = COMPOSE_REPO.download_ref(ref, output_dir=tmp_path)
        except urllib.error.URLError as papa:
            raise InstallerError(papa) from None
        arch = zipfile.ZipFile(arch_path)
        dir_name = arch.namelist()[0]
        arch.extractall(path=tmp_path)
        shutil.move(src=tmp_path / dir_name, dst=LOCAL_PATH)
    print()

    glob_iters = [BIN_DIR.glob(ptrn) for ptrn in SCRIPT_SUFFIXES]
    print('Making scripts executable:')
    for script in itertools.chain(*glob_iters):
        print(f'  - {script}')
        script.chmod(0o755)
    print()


def configure() -> None:
    ...


def run() -> None:
    cmd = ' '.join(ENTRYPOINT)
    print(f'Running {cmd}')
    sys.stdout.flush()
    sys.stderr.flush()
    os.chdir(LOCAL_PATH)
    os.execv(ENTRYPOINT[0], ENTRYPOINT)


def main() -> None:
    try:
        download()
        configure()
        run()
    except InstallerError as papa:
        print_err('', papa, '', 'Exit now', '')
        sys.exit(1)


if __name__ == '__main__':
    main()
