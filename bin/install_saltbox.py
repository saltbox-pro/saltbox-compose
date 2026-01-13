#! /usr/bin/env python3

# TODO Extra modules
# TODO Interactive
# TODO Alternative obtaining with Git
# TODO Should it deal with upgrades?
# TODO Offline mode with images

import argparse
import functools
import ipaddress
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Type, TypeVar

ENC='UTF-8'
HTTP_CHUNK_BYTE = 8192
HTTP_TIMEOUT_SEC = 30
COMPOSE_DEFAULT_REF = 'RELEASE'
VERSION_TAG_PATTERN = re.compile(r'^v\d+\.\d+\.\d+.*$')
LOCAL_PATH = Path('./saltbox-compose/')
BIN_DIR = LOCAL_PATH / 'bin'
ENV_OVERRIDE = LOCAL_PATH / 'override.env'
SCRIPT_SUFFIXES = ('*.sh', '*.py',)
# Uses after changind CWD
ENTRYPOINT = ['bin/update_and_run.sh', '--no-root', '--force', '--detach', '--no-git-pull']  # TODO Parametric flags
MIN_DOCKER_VERSION = '25.0.0'
MIN_COMPOSE_VERSION = '2.20.2'
MIN_PYTHON_VERSION = '3.7.3'

URLS = {
    'saltbox-compose': 'https://dev.saltbox.pro/saltbox/saltbox-compose',
}

cache = functools.lru_cache(maxsize=None)


class InstallerError(RuntimeError): ...

def print_out(*args) -> None:
    print(*args, file=sys.stdout, sep='\n')

def print_err(*args) -> None:
    print(*args, file=sys.stderr, sep='\n')


@dataclass
class Config:
    MIN_PORT = 1
    MAX_PORT = 2**16 - 1
    HOSTNAME_LABEL_PATTERN = re.compile(r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$')

    host: str = 'saltbox.local'
    port: int = 443

    def validate(self) -> None:
        if not self.MIN_PORT <= self.port <= self.MAX_PORT:
            raise ValueError(f'Port {self.port} is out of range {self.MIN_PORT}-{self.MAX_PORT}')
        self._validate_host()

    @property
    def is_host_seems_ip(self) -> bool:
        try:
            ipaddress.ip_address(self.host)
        except ValueError:
            return False
        return True

    def _validate_host(self) -> None:
        if self.is_host_seems_ip:
            return
        if len(self.host) > 255:
            raise ValueError('Too long DNS name')
        elif not self.host:
            raise ValueError('Empty hostname')
        for part in self.host.split('.'):
            if not self.HOSTNAME_LABEL_PATTERN.match(part):
                dosa = f'Hostname part `{part}` seems not valid'
                raise ValueError(dosa)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=('Run Salt.Box Docker Compose based instance from scratch'),
    )
    parser.add_argument(
        'overrides',
        nargs='*',
        type=str,
        help="Extra values to include into dotenv in form of NAME='VAL'",
    )
    parser.add_argument(
        '--host',
        type=str,
        help=f'Hostname or real address to serve on, `{Config.host}` by default',
    )
    parser.add_argument(
        '--host-is-name',
        action='store_true',
        help='Force SSL cert for DNS name even if `host` looks like IP address'
    )
    parser.add_argument(
        '--port',
        type=int,
        help=f'Port to serve HTTPS, `{Config.port}` by default',
    )
    # TODO Impl
    parser.add_argument(
        '-n', '--non-interactive',
        action='store_true',
        help='Do not ask to input, use defaults',
    )
    parser.add_argument(
        '-s', '--skip-check',
        action='store_true',
        help='Do not check Docker install before run',
    )
    parser.add_argument(
        '-u', '--skip-run',
        action='store_true',
        help='Prepare but not run',
    )
    return parser.parse_args()


VersionSelf = TypeVar('VersionSelf', bound='Version')
class Version:
    """ Represents simplified SemVer (3 main numbers only)"""
    # Simplified official regex https://regex101.com/r/Ly7O1x/3/
    PATTERN = re.compile(r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)([-+].*)?$')

    def __init__(self, major: int, minor: int, patch: int) -> None:
        self._version = (major, minor, patch,)

    @property
    def major(self) -> int:
        return self._version[0]

    @property
    def minor(self) -> int:
        return self._version[1]

    @property
    def patch(self) -> int:
        return self._version[2]

    @classmethod
    def from_str(cls: Type[VersionSelf], version: str) -> VersionSelf:
        match = Version.PATTERN.match(version)
        if not match:
            dosa = f'Version string `{version}` failed to be parsed as SemVer'
            raise InstallerError(dosa)
        obj = cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
        )
        return obj

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}.{self.patch}'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._version == self._version

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        for i in range(len(self._version)):
            if self._version[i] < other._version[i]:
                return True
            elif self._version[i] > other._version[i]:
                return False
        return False


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

def check(args: argparse.Namespace) -> None:
    if args.skip_check:
        print_out('Skipping requirements checkup!', '')
        return

    py_ver = Version(
        major=sys.version_info.major,
        minor=sys.version_info.minor,
        patch=sys.version_info.micro,
    )
    min_py_ver = Version.from_str(MIN_PYTHON_VERSION)
    print_out(f'Running on Python version `{py_ver}`')
    if py_ver < min_py_ver:
        raise InstallerError(f'Minimal required Python version is v{MIN_PYTHON_VERSION}')

    docker_cmd = ['docker', 'version', '--format', '{{.Server.Version}}']
    compose_cmd = ['docker', 'compose', 'version', '--short']

    try:
        proc = subprocess.run(docker_cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise InstallerError('Not found `docker` command. Not installed or not in PATH?')
    except OSError as err:
        raise InstallerError(err)
    if proc.returncode != 0:
        print_err(proc.stderr)
        dosa = f'Command `{" ".join(docker_cmd)}` failed. May be use `sudo` to run as root?'
        raise InstallerError(dosa)

    docker_ver_str = proc.stdout.strip()
    print_out(f'Docker version string is `{docker_ver_str}`')
    docker_ver = Version.from_str(docker_ver_str)
    min_docker_ver = Version.from_str(MIN_DOCKER_VERSION)
    if docker_ver < min_docker_ver:
        raise InstallerError(f'At least Docker v{MIN_DOCKER_VERSION} required')

    try:
        proc = subprocess.run(compose_cmd, capture_output=True, text=True)
    except OSError as err:
        raise InstallerError(err)
    if proc.returncode != 0:
        print_err(proc.stderr)
        dosa = f'Command `{" ".join(compose_cmd)}` failed. Is Docker Compose installed?'
        raise InstallerError(dosa)

    compose_ver_str = proc.stdout.strip()
    print_out(f'Docker Compose version string is `{compose_ver_str}`')
    compose_ver = Version.from_str(compose_ver_str)
    min_compose_ver = Version.from_str(MIN_COMPOSE_VERSION)
    min_docker_ver = Version.from_str(MIN_DOCKER_VERSION)
    if compose_ver < min_compose_ver:
        raise InstallerError(f'At least Docker Compose v{MIN_COMPOSE_VERSION} required')

    print_out()


def download(args: argparse.Namespace) -> None:
    if LOCAL_PATH.exists():
        dosa = f'Already exists: {LOCAL_PATH}'
        raise InstallerError(dosa)

    # TODO Refs: latest, tag, branch, arbitrary
    if COMPOSE_DEFAULT_REF == 'RELEASE':
        ref = COMPOSE_REPO.get_latest_version_tag()
    else:
        ref = COMPOSE_DEFAULT_REF

    print_out('Downloading Salt.Box Compose...')
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_path = Path(tmp_dir_name)
        try:
            arch_path = COMPOSE_REPO.download_ref(ref, output_dir=tmp_path)
        except urllib.error.URLError as papa:
            raise InstallerError(papa) from None
        arch = zipfile.ZipFile(arch_path)
        dir_name = arch.namelist()[0]
        arch.extractall(path=tmp_path)
        shutil.move(src=str(tmp_path / dir_name), dst=LOCAL_PATH)
    print_out()

    glob_iters = [BIN_DIR.glob(ptrn) for ptrn in SCRIPT_SUFFIXES]
    print('Making scripts executable:')
    for script in itertools.chain(*glob_iters):
        print(f'  - {script}')
        script.chmod(0o755)
    print_out()


def configure(args: argparse.Namespace) -> None:
    conf = Config()
    if args.host is not None:
        conf.host = args.host
    if args.port is not None:
        conf.port = args.port
    try:
        conf.validate()
    except ValueError as err:
        raise InstallerError(err) from err

    override = [f"WEB_SERVER_OUTER_SOCKET='{conf.host}:{conf.port}'"]
    if conf.is_host_seems_ip and not args.host_is_name:
        override.append(f"WEB_SERVER_SSL_ALT_NAMES_IP='127.0.0.1,{conf.host}'")
    else:
        override.append(f"WEB_SERVER_SSL_ALT_NAMES_DNS='localhost,{conf.host}'")

    override.extend(args.overrides)

    with ENV_OVERRIDE.open('w', encoding=ENC) as fstream:
        fstream.write('\n'.join(override) + '\n')

    print_out(f'Override file `{ENV_OVERRIDE}` has been saved', '')


def run(args: argparse.Namespace) -> None:
    cmd = ' '.join(ENTRYPOINT)
    print_out(f'Running {cmd}', '')
    sys.stdout.flush()
    sys.stderr.flush()
    if args.skip_run:
        print_out('Skipping run!', '')
        return
    os.chdir(LOCAL_PATH)
    os.execv(ENTRYPOINT[0], ENTRYPOINT)


def main() -> None:
    args = get_args()

    print_out()

    try:
        check(args)
        download(args)
        configure(args)
        run(args)
    except InstallerError as papa:
        print_err('', papa, '', 'Exit on error', '')
        sys.exit(1)


if __name__ == '__main__':
    main()
