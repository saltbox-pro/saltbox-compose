#! /usr/bin/env python3

# Copyright 2025, 2026 Anton Karmanov

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The script is a part of Salt.Box Compose
"""

# TODO Extra modules
# TODO Alternative obtaining with Git
# TODO Should it deal with upgrades?
# TODO Offline mode with images

import argparse
import contextlib
import functools
import http
import ipaddress
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Type, TypeVar

ENC='UTF-8'
HTTP_CHUNK_BYTE = 8192
HTTP_TIMEOUT_SEC = 30
VERSION_TAG_PATTERN = re.compile(r'^v\d+\.\d+\.\d+.*$')
LOCAL_PATH = Path('./saltbox-compose/')
BIN_DIR = LOCAL_PATH / 'bin'
ENV_OVERRIDE = LOCAL_PATH / 'override.env'
SCRIPT_SUFFIXES = ('*.sh', '*.py',)
ADMIN_SECRET_NAME = 'saltbox_admin_password'

# Uses after changind CWD
CLEANUP_CMD = ['./bin/sb-compose.sh', 'down', '--volumes', '--remove-orphans']
PREMAKE_SECRETS_CMD = ['bin/make_secrets.py']
ENTRYPOINT = ['bin/update_and_run.sh', '--no-root', '--force', '--detach', '--no-git-pull']

MIN_DOCKER_VERSION = '25.0.0'
MIN_COMPOSE_VERSION = '2.20.2'
MIN_PYTHON_VERSION = '3.7.3'

URLS = {
    'saltbox-compose': 'https://dev.saltbox.pro/saltbox/saltbox-compose',
}

SWITCHABLE_IMAGE_TAGS = [
    'FRONTEND_IMAGE_TAG',
    'GATEWAY_IMAGE_TAG',
    'KEYCLOAK_IMAGE_TAG',
    'MAKE_CERTS_IMAGE_TAG',
    'MONGODB_IMAGE_TAG',
    'NGINX_IMAGE_TAG',
    'OPA_IMAGE_TAG',
    'PROXY_IMAGE_TAG',
    'REDIS_IMAGE_TAG',
    'SALT_MASTER_IMAGE_TAG',
    'SSHFS_IMAGE_TAG',
]

cache = functools.lru_cache(maxsize=None)


class InstallerError(RuntimeError): ...
class HttpNotFoundError(InstallerError): ...


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=('Run Salt.Box Docker Compose based instance from scratch'),
    )
    parser.add_argument(
        'OVERRIDE',
        nargs='*',
        type=str,
        help="Extra values to include into dotenv in form of NAME='VAL'",
    )
    parser.add_argument(
        '--admin',
        type=str,
        help='The Salt.Box Administrator\'s login',
    )
    parser.add_argument(
        '--compose-ref',
        type=str,
        help=(
            'Salt.Box Compose Git reference to obtain, '
            '`RELEASE` to search fo latest release tag, '
            f'`{Config.compose_ref}` by default'
        )
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help=(
            'Cleanup possibly existing Salt.Box instance '
            'with the same COMPOSE_PROJECT_NAME. '
            'BEWARE DATA LOST!'
        ),
    )
    parser.add_argument(
        '--explicit-secret',
        action='append',
        default=[],
        help=(
            'Set a secret value explicitly in form of `NAME=VALUE`, '
            f'use `{ADMIN_SECRET_NAME}=VALUE` to set the Salt.Box Administrator\'s password. '
            'Can be specified multiple times.'
        ),
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
        '--keep-image-tags',
        action='store_true',
        help=f'Do not switch image tags for {Config.DEV_BRANCH}',
    )
    parser.add_argument(
        '--port',
        type=int,
        help=f'Port to serve HTTPS, `{Config.port}` by default',
    )
    parser.add_argument(
        '-n', '--non-interactive',
        action='store_true',
        help='Do not ask to input, use defaults',
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Do not show downloading progress, CI-friendly',
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
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print more info',
    )
    return parser.parse_args()

VERBOSE=False


@contextlib.contextmanager
def cd(path: Path):
    orig = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(orig)


def run_cmd(cmd: List[str]) -> None:
    cmd_str = ' '.join(cmd)
    print_out(f'Running `{cmd_str}`', '')
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as err:
        raise InstallerError(err) from None


def print_out(*args, verbose: bool=False) -> None:
    if verbose and not VERBOSE:
        return
    print(*args, file=sys.stdout, sep='\n')


def print_err(*args, verbose: bool=False) -> None:
    if verbose and not VERBOSE:
        return
    print(*args, file=sys.stderr, sep='\n')


class Interactions:
    def __init__(self, non_interactive=False) -> None:
        self.non_interactive = non_interactive

    def ask(self, prompt: str, default: Optional[str] = None) -> str:
        if self.non_interactive:
            if default is None:
                dosa = f'No data for prompt `{prompt}`'
                raise InstallerError(dosa)
            return default

        if default is None:
            prompt = f'{prompt}: '
        else:
            prompt = f'{prompt} [{default}]: '
        val = input(prompt).strip()

        if not val:
            if default is None:
                raise InstallerError('Expected input, but empty string recieved')
            else:
                return default

        return val

    def ask_optional(self, prompt: str) -> Optional[str]:
        if self.non_interactive:
            return None
        prompt = f'{prompt}: '
        val = input(prompt).strip()
        return val or None

    def ask_int(self, prompt: str, default: Optional[int] = None) -> int:
        val = self.ask(prompt, default=str(default))
        try:
            return int(val)
        except ValueError as err:
            raise InstallerError(err) from None


    def ask_confirm(self, prompt: str, default: bool = True) -> bool:
        if self.non_interactive:
            return True

        yn = 'Y/n' if default else 'y/N'

        while True:
            resp = input(f'{prompt} [{yn}]: ').strip().lower()
            if not resp:
                return default
            elif resp in ('y', 'yes',):
                return True
            elif resp in ('n', 'no',):
                return False
            print_err('Unexpected input')


@dataclass
class Config:
    MIN_PORT = 1
    MAX_PORT = 2**16 - 1
    HOSTNAME_LABEL_PATTERN = re.compile(r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$')

    STABLE_BRANCH = 'master'
    DEV_BRANCH = 'dev'
    RELEASE_REF = 'RELEASE'

    cleanup: bool = False
    host: str = 'saltbox.local'
    port: int = 443
    compose_ref = RELEASE_REF
    force_host_as_name: bool = False
    admin_name: str = 'master'
    set_image_tags: bool = False

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

    @property
    def is_host_ip(self) -> bool:
        return self.is_host_seems_ip and not self.force_host_as_name

    def _validate_host(self) -> None:
        if self.is_host_ip:
            return
        if len(self.host) > 255:
            raise ValueError('Too long DNS name')
        elif not self.host:
            raise ValueError('Empty hostname')
        if not self.compose_ref:
            raise ValueError('Empty compose_ref')
        for part in self.host.split('.'):
            if not self.HOSTNAME_LABEL_PATTERN.match(part):
                dosa = f'Hostname part `{part}` seems not valid'
                raise ValueError(dosa)

    def __str__(self) -> str:
        data = [f'Serve on: `{self.host}:{self.port}`']
        if self.is_host_seems_ip:
            wut = 'a DNS name' if self.force_host_as_name else 'an IP address'
            data[0] += f' (Host part is treated as {wut})'
        data.append(f'Salt.Box Compose reference is: `{self.compose_ref}`')
        data.append(f'Salt.Box Administrator\'s login is: `{self.admin_name}`')
        data.append('Salt.Box Administrator\'s password is: [ SEARCH IN FURTHER OUTPUT ]')
        data.append(f'Cleanup: {"YES!!! " if self.cleanup else "no"}')
        return '\n'.join(data)


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


def _download_file(resp: http.client.HTTPResponse, output: Path, progress: bool) -> None:
    def print_progress():
        if total:
            pct = downloaded * 100 / total
            sys.stdout.write(f'\r{downloaded}/{total} bytes ({pct:.1f}%)')
        else:
            sys.stdout.write(f'\r{downloaded} bytes')
        sys.stdout.flush()

    cont_len = resp.getheader('Content-Length')
    if cont_len and cont_len.isdigit():
        total = int(cont_len)
    else:
        total = None
    downloaded = 0
    with output.open('wb') as file:
        while True:
            data = resp.read(HTTP_CHUNK_BYTE)
            if not data:
                print_progress()
                break
            file.write(data)
            downloaded += len(data)
            if progress:
                print_progress()
    sys.stdout.write('\n')


def download_file(url: str, output: Path, progress: bool) -> None:
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
            _download_file(resp=resp, output=output, progress=progress)
    except urllib.error.HTTPError as papa:
        if papa.code == 404:
            dosa = 'Not found: {url}'
            raise HttpNotFoundError(dosa) from None
        dosa = f'HTTP error on `GET {url}`: {papa}'
        raise InstallerError(dosa) from None
    except urllib.error.URLError as papa:
        dosa = f'Network error on `GET {url}`: {papa}'
        raise InstallerError(dosa) from None


class GitLabRepo:
    ARCHIVE_SUFFIX = 'zip'  # Supposed to be better on error detection

    def __init__(self, url: str, progress: bool = True) -> None:
        url_obj = urllib.parse.urlparse(url)
        path = Path(url_obj.path)
        self.scheme = url_obj.scheme
        self.server = url_obj.netloc
        self.owner = str(path.parent).lstrip('/')
        self.project = path.name
        self.progress = progress

    @property
    def api_url(self) -> str:
        return f'{self.scheme}://{self.server}/api/v4'

    @cache
    def get_tags(self) -> List[str]:
        url = f'{self.api_url}/projects/{self.owner}%2F{self.project}/repository/tags'
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

    def filename_for_ref(self, ref: str) -> str:
        return f'{self.project}-{ref}.{self.ARCHIVE_SUFFIX}'

    def url_for_ref(self, ref: str) -> str:
        filename = self.filename_for_ref(ref)
        url = f'{self.scheme}://{self.server}/{self.owner}/{self.project}/-/archive/{ref}/{filename}'
        return url

    def download_ref(self, ref: str, output_dir: Path = Path()) -> None:
        """
        Get code of ref version with no Git

        :raises HttpNotFoundError: on 404
        :raises InstallerError: on HTTP or network errors
        """
        url = self.url_for_ref(ref)

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_path = Path(tmp_dir_name)
            arch_path = tmp_path / self.filename_for_ref(ref)
            try:
                download_file(url, output=arch_path, progress=self.progress)
            except HttpNotFoundError:
                dosa = f'Server returns `Not found` for Compose ref `{ref}`'
                raise InstallerError(dosa) from None
            arch = zipfile.ZipFile(arch_path)
            dir_name = arch.namelist()[0]
            arch.extractall(path=tmp_path)
            shutil.move(src=str(tmp_path / dir_name), dst=output_dir)


COMPOSE_REPO = GitLabRepo(URLS['saltbox-compose'])


@dataclass
class AddonModule:
    name: str
    repo: GitLabRepo
    base_dir: str
    license: str
    compose_files: List[str]
    env_file: str
    is_token_required: bool
    switchable_image_tags: List[str]
    secret_configs: List[str] = field(default_factory=list)
    ref: str = Config.RELEASE_REF


ADDON_MODULES = [
    AddonModule(
        name='Inventory',
        repo=GitLabRepo(url='https://dev.saltbox.pro/saltbox/saltbox-inventory-compose'),
        base_dir='saltbox-inventory-compose',
        switchable_image_tags=['INVENTORY_IMAGE_TAG'],
        compose_files=['compose.yaml'],
        env_file='.env',
        secret_configs=['secrets.json'],
        license='EULA',  # =(
        is_token_required=True,
    ),
    AddonModule(
        name='Metric',
        repo=GitLabRepo(url='https://dev.saltbox.pro/saltbox/saltbox-metric-compose'),
        base_dir='saltbox-inventory-compose',
        switchable_image_tags=['METRIC_IMAGE_TAG'],
        compose_files=['compose.yaml'],
        env_file='.env',
        license='EULA',  # =(
        is_token_required=True,
    ),
    AddonModule(
        name='Scheduler',
        repo=GitLabRepo(url='https://dev.saltbox.pro/saltbox/saltbox-scheduler-compose'),
        base_dir='saltbox-scheduler-compose',
        switchable_image_tags=['SCHEDULER_IMAGE_TAG'],
        compose_files=['compose.yaml'],
        env_file='.env',
        secret_configs=['secrets.json'],
        license='EULA',  # =(
        is_token_required=True,
    ),
]


def configure_script(args: argparse.Namespace, interactions: Interactions) -> Config:
    conf = Config(force_host_as_name=args.host_is_name)
    cmd: List[str] = ['./install_saltbox.py']
    if not args.non_interactive:
        cmd.append('--non-interactive')
    cmd += sys.argv[1:]

    if args.host is not None:
        conf.host = args.host
    else:
        conf.host = interactions.ask('Real address or name', conf.host)
        cmd += ['--host', conf.host]

    if args.port is not None:
        conf.port = args.port
    else:
        conf.port = interactions.ask_int('Port to serve HTTPS', conf.port)
        cmd += ['--port', str(conf.port)]

    if args.compose_ref is not None:
        conf.compose_ref = args.compose_ref
    else:
        conf.compose_ref = interactions.ask('Salt.Box reference', conf.compose_ref)
        cmd += ['--compose-ref', conf.compose_ref]

    if conf.compose_ref == Config.RELEASE_REF:
        conf.compose_ref = COMPOSE_REPO.get_latest_version_tag()

    if args.admin is not None:
        conf.admin_name = args.admin
    else:
        conf.admin_name = interactions.ask('Salt.Box Administrator\'s login', conf.admin_name)
        cmd += ['--admin', conf.admin_name]

    if not any(x.startswith(f'{ADMIN_SECRET_NAME}=') for x in args.explicit_secret):
        admin_pass = interactions.ask_optional(
            'Salt.Box Administartor\'s password (leave empty to generate)')
        if admin_pass is not None:
            admin_secret=f'{ADMIN_SECRET_NAME}={admin_pass}'
            args.explicit_secret.append(admin_secret)
            cmd += ['--explicit-secret', admin_secret]

    if not args.keep_image_tags and conf.compose_ref == Config.DEV_BRANCH:
        conf.set_image_tags = interactions.ask_confirm(
            f'Select tag `{args.compose_ref}` for main images?')
        if not conf.set_image_tags:
            cmd.append('--keep-image-tags')

    if not args.cleanup:
        conf.cleanup = interactions.ask_confirm(
            'Cleanup possibly existing instance? (DATA LOST!)', default=False)
        if conf.cleanup:
            cmd.append('--cleanup')
    else:
        conf.cleanup = args.cleanup

    try:
        conf.validate()
    except ValueError as err:
        raise InstallerError(err) from err

    print_out('', conf, '')

    cmd_str = ' '.join(cmd)
    print(f'Command to repeat with no dialog:\n\n  $ {cmd_str}\n')

    if not interactions.ask_confirm('Continue?'):
        raise InstallerError('Cancelled by user')

    return conf

def check(args: argparse.Namespace) -> None:
    if LOCAL_PATH.exists():
        dosa = f'Already exists: {LOCAL_PATH}'
        raise InstallerError(dosa)

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
        dosa = 'Not found `docker` command. Not installed or not in PATH?'
        raise InstallerError(dosa) from None
    except OSError as err:
        raise InstallerError(err) from None
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
        raise InstallerError(err) from None
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


def download(args: argparse.Namespace, config: Config) -> None:
    print_out(f'Downloading Salt.Box Compose reference `{config.compose_ref}`...')
    print_out(f'URL: {COMPOSE_REPO.url_for_ref(config.compose_ref)}', verbose=True)
    COMPOSE_REPO.download_ref(config.compose_ref, output_dir=LOCAL_PATH)
    print_out()

    glob_iters = [BIN_DIR.glob(ptrn) for ptrn in SCRIPT_SUFFIXES]
    print_out('Making scripts executable:')
    for script in itertools.chain(*glob_iters):
        print_out(f'  - {script}')
        script.chmod(0o755)
    print_out()


def configure_system(args: argparse.Namespace, config: Config) -> None:
    override = []

    if config.set_image_tags:
        for img_tag in SWITCHABLE_IMAGE_TAGS:
            override.append(f"{img_tag}='{config.compose_ref}'")

    override += [
        f"SALTBOX_ADMIN_USERNAME='{config.admin_name}'",
        f"WEB_SERVER_OUTER_SOCKET='{config.host}:{config.port}'"
    ]
    if config.is_host_seems_ip and not config.force_host_as_name:
        override.append(f"WEB_SERVER_SSL_ALT_NAMES_IP='127.0.0.1,{config.host}'")
    else:
        override.append(f"WEB_SERVER_SSL_ALT_NAMES_DNS='localhost,{config.host}'")

    override.extend(args.OVERRIDE)

    with ENV_OVERRIDE.open('w', encoding=ENC) as fstream:
        fstream.write('\n'.join(override) + '\n')

    print_out(f'Override file `{ENV_OVERRIDE}` has been saved', '')


def run(args: argparse.Namespace, config: Config) -> None:
    ep_cmd = ENTRYPOINT.copy()
    if args.no_progress:
        ep_cmd.append('--no-progress')

    if config.cleanup:
        env_cmd = ep_cmd.copy()
        env_cmd.append('--only-env')
        run_cmd(env_cmd)
        run_cmd(CLEANUP_CMD)

    if args.explicit_secret:
        cmd = PREMAKE_SECRETS_CMD.copy()
        for val in args.explicit_secret:
            cmd += ['--explicit', val]
        run_cmd(cmd)
    ep_cmd_str = ' '.join(ep_cmd)
    print_out(f'Running `{ep_cmd_str}`', '')
    sys.stdout.flush()
    sys.stderr.flush()
    if args.skip_run:
        print_out('Skipping run!', '')
        return
    os.execv(ep_cmd[0], ep_cmd)


def main() -> None:
    global VERBOSE
    args = get_args()
    VERBOSE = args.verbose
    interactions = Interactions(non_interactive=args.non_interactive)
    COMPOSE_REPO.progress = not args.no_progress

    msg = '\nNon-interactive mode, no confirmations will be asked!' if interactions.non_interactive else ''
    print_out(msg)

    try:
        check(args)
        conf = configure_script(args, interactions=interactions)
        download(args, config=conf)
        configure_system(args, config=conf)
        with cd(LOCAL_PATH):
            time.sleep(0.04)  # To avoid missing executables in `./bin/`
            run(args, config=conf)
    except InstallerError as papa:
        print_err('', papa, '', 'Exit on error', '')
        sys.exit(1)


if __name__ == '__main__':
    main()
