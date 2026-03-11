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

# TODO Alternative obtaining with Git
# TODO Offline mode with images
# TODO Check 'vm.overcommit_memory=1'

import argparse
import contextlib
import dataclasses
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
import textwrap
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, ClassVar, List, Optional, Type, TypeVar

ENC = 'UTF-8'
INDENT = 2 * ' '
HTTP_CHUNK_BYTE = 8192
HTTP_TIMEOUT_SEC = 30
VERSION_TAG_PATTERN = re.compile(r'^v\d+\.\d+\.\d+.*$')
LOCAL_PATH = Path('./saltbox-compose/')
BIN_DIR = LOCAL_PATH / 'bin'
ENV_OVERRIDE = LOCAL_PATH / 'override.env'
SCRIPT_SUFFIXES = ('*.sh', '*.py',)
ADMIN_SECRET_NAME = 'saltbox_admin_password'
RELEASE_REF = 'RELEASE'
REGISTRY_DOTENV_VAR='IMAGE_REGISTRY'

# Uses after changind CWD
CLEANUP_CMD = ['./bin/sb-compose.sh', 'down', '--volumes', '--remove-orphans']
PREMAKE_SECRETS_CMD = ['bin/make_secrets.py']
ENTRYPOINT = ['bin/update_and_run.sh', '--no-root', '--force', '--detach', '--no-git-pull']

MIN_DOCKER_VERSION = '25.0.0'
MIN_COMPOSE_VERSION = '2.20.2'
MIN_PYTHON_VERSION = '3.7.3'

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

TOKEN_NAME = 'SALTBOX_INSTALL_TOKEN'
# GitLab group token MUST have scopes: read_repository, read_registry, read_api
TOKEN = os.environ.get(TOKEN_NAME)

class InstallerError(RuntimeError): ...
class HttpNotFoundError(InstallerError): ...


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run Salt.Box Docker Compose based instance from scratch',
        epilog=f'Set `{TOKEN_NAME}` environment variable to use access token for proprietary modules',
    )
    parser.add_argument(
        'OVERRIDE',
        nargs='*',
        type=str,
        help="Extra values to include into dotenv in form of NAME='VAL'",
    )
    parser.add_argument(
        '--addons',
        action='store_true',
        help=(
            f'Install also official Salt.Box Addons: {", ".join(a.name for a in ADDON_MODULES)}. '
            'ADDONS ARE PROPRIETARY, TOKEN REQUIRED.'  # =(
        )
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
            f'`{RELEASE_REF}` to search fo latest release tag, '
            f'`{Config.STABLE_BRANCH}` and `{Config.DEV_BRANCH}` '
            'for main dev-branches. '
            f'`{Config.compose_ref}` by default.'
        )
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help=(
            'Cleanup possibly existing Salt.Box instance '
            'with the same COMPOSE_PROJECT_NAME. '
            'BEWARE OF DATA LOST!'
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
        '--keep-addon-tags',
        action='store_true',
        help='Do not switch addon tags to branches',
    )
    parser.add_argument(
        '--keep-image-tags',
        action='store_true',
        help=f'Do not switch image tags to `{Config.DEV_BRANCH}`',
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
def cd(path: Optional[Path]):
    if path is None:
        yield
        return
    orig = Path.cwd()
    os.chdir(path)
    time.sleep(0.04)  # To workaround unupdated CWD
    try:
        yield
    finally:
        os.chdir(orig)


def run_cmd(cmd: List[str], input: Optional[str] = None) -> None:
    cmd_str = ' '.join(cmd)
    print_out(f'Running `{cmd_str}`', '')
    try:
        subprocess.run(cmd, input=input, check=True, text=True)
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


def get_dotenv_var(name: str, dotenv: Path=Path('.env')) -> str:
    """ Read str value from env-file """
    cmd = ['sh', '-c', f'. \'{dotenv.absolute()}\' && printf \'%s\' "${name}"']
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    val = proc.stdout
    print_out(f'Got dotenv var `{name}`: `{val}`', verbose=True)
    return val


class Interactions:
    def __init__(self, non_interactive=False) -> None:
        self.non_interactive = non_interactive

    def ask(self, prompt: str, default: Optional[str] = None) -> str:
        if default is None:
            prompt = f'{prompt}: '
        else:
            prompt = f'{prompt} [{default}]: '
        if self.non_interactive:
            if default is None:
                dosa = f'No data for prompt `{prompt}`'
                raise InstallerError(dosa)
            print_out(f'{prompt}{default}')
            return default

        val = input(prompt).strip()

        if not val:
            if default is None:
                raise InstallerError('Expected input, but empty string recieved')
            else:
                return default

        return val

    def ask_optional(self, prompt: str) -> Optional[str]:
        prompt = f'{prompt}: '
        if self.non_interactive:
            print_out(prompt)
            return None
        val = input(prompt).strip()
        return val or None

    def ask_int(self, prompt: str, default: int) -> int:
        val = self.ask(prompt, default=str(default))
        try:
            return int(val)
        except ValueError as err:
            raise InstallerError(err) from None


    def ask_confirm(self, prompt: str, default: bool = True) -> bool:
        yn = 'Y/n' if default else 'y/N'
        prompt = f'{prompt} [{yn}]: '
        if self.non_interactive:
            val = 'Y' if default else 'N'
            print_out(f'{prompt}{val}')
            return default

        while True:
            resp = input().strip().lower()
            if not resp:
                return default
            elif resp in ('y', 'yes',):
                return True
            elif resp in ('n', 'no',):
                return False
            print_err('Unexpected input')


@dataclasses.dataclass
class Config:
    MIN_PORT = 1
    MAX_PORT = 2**16 - 1
    HOSTNAME_LABEL_PATTERN = re.compile(r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$')

    STABLE_BRANCH = 'master'
    DEV_BRANCH = 'dev'
    SUPPORTED_REFS: ClassVar = [RELEASE_REF, STABLE_BRANCH, DEV_BRANCH]

    cleanup: bool = False
    host: str = 'saltbox.local'
    port: int = 443
    compose_ref = RELEASE_REF
    force_host_as_name: bool = False
    admin_name: str = 'master'
    extra_override: List['str'] = dataclasses.field(default_factory=list)
    set_image_tags: bool = False
    selected_addons: List['AddonModule'] = dataclasses.field(default_factory=list)
    registry_user: str = 'install_saltbox'

    def validate(self) -> None:
        if not self.MIN_PORT <= self.port <= self.MAX_PORT:
            dosa = f'Port {self.port} is out of range {self.MIN_PORT}-{self.MAX_PORT}'
            raise ValueError(dosa)
        self._validate_host()
        if TOKEN is None and self.is_token_required:
            dosa = f'Missing required `{TOKEN_NAME}` env variable'
            raise ValueError(dosa)

    @property
    def is_token_required(self) -> bool:
        return any(a.is_token_required for a in self.selected_addons)

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
        if self.selected_addons:
            addons_str = ', '.join(f'{a.name} ({a.license})' for a in self.selected_addons)
            data.append(f'Add-on modules: {addons_str}')
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


def download_file(request: urllib.request.Request, output: Path, progress: bool) -> None:
    try:
        with urllib.request.urlopen(url=request, timeout=HTTP_TIMEOUT_SEC) as resp:
            _download_file(resp=resp, output=output, progress=progress)
    except urllib.error.HTTPError as papa:
        if papa.code == 404:
            dosa = 'Not found: {url}'
            raise HttpNotFoundError(dosa) from None
        dosa = f'HTTP error on `GET {request.full_url}`: {papa}'
        raise InstallerError(dosa) from None
    except urllib.error.URLError as papa:
        dosa = f'Network error on `GET {request.full_url}`: {papa}'
        raise InstallerError(dosa) from None


class GitLabRepo:
    ARCHIVE_SUFFIX = 'zip'  # Supposed to be better on error detection

    def __init__(self, url: str, token: Optional[str] = None, progress: bool = True) -> None:
        self.token = token
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
        request = urllib.request.Request(url=url)
        if self.token:
            request.headers['PRIVATE-TOKEN'] = self.token
        try:
            resp = urllib.request.urlopen(url=request)
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
        params = urllib.parse.urlencode({'sha': ref})
        return (
            f'{self.api_url}/projects/{self.owner}%2F{self.project}/repository/'
            f'archive.{self.ARCHIVE_SUFFIX}?{params}'
        )

    def download_ref(self, ref: str, output_dir: Path = Path()) -> None:
        """
        Get code of ref version with no Git

        :raises HttpNotFoundError: on 404
        :raises InstallerError: on HTTP or network errors
        """
        url = self.url_for_ref(ref)
        request = urllib.request.Request(url)
        if self.token:
            request.headers['PRIVATE-TOKEN'] = self.token

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_path = Path(tmp_dir_name)
            arch_path = tmp_path / self.filename_for_ref(ref)
            try:
                download_file(request=request, output=arch_path, progress=self.progress)
            except HttpNotFoundError:
                dosa = f'Server returns `Not found` for Compose ref `{ref}`'
                raise InstallerError(dosa) from None
            if not zipfile.is_zipfile(arch_path):
                data = arch_path.read_text(encoding=ENC)
                print_err(f'Content of `{arch_path}`:', data)
                dosa = f'Downloaded code archive is not a {self.ARCHIVE_SUFFIX} file'
                raise InstallerError(dosa)
            arch = zipfile.ZipFile(arch_path)
            dir_name = arch.namelist()[0]
            destination_full = output_dir / dir_name
            if destination_full.exists():
                dosa = f'Already exists: `{destination_full}`'
                raise InstallerError(dosa)
            arch.extractall(path=tmp_path)
            shutil.move(src=str(tmp_path / dir_name), dst=output_dir)


COMPOSE_REPO = GitLabRepo(url='https://dev.saltbox.pro/saltbox/saltbox-compose', token=TOKEN)


@cache
def resolve_ref(ref: str, repo: GitLabRepo) -> str:
    """ Resolves RELEASE_REF special value """
    if ref == RELEASE_REF:
        return repo.get_latest_version_tag()
    return ref


@dataclasses.dataclass
class AddonModule:
    name: str
    repo: GitLabRepo
    base_dir: str
    license: str
    compose_files: List[str]
    env_file: str
    is_token_required: bool
    switchable_image_tags: List[str]
    secrets_configs: List[str] = dataclasses.field(default_factory=list)
    ref: str = RELEASE_REF


ADDON_MODULES = [
    AddonModule(
        name='Inventory',
        repo=GitLabRepo(
            url='https://dev.saltbox.pro/saltbox/saltbox-inventory-compose',
            token=TOKEN,
        ),
        base_dir='saltbox-inventory-compose',
        switchable_image_tags=['INVENTORY_IMAGE_TAG'],
        compose_files=['compose.yaml'],
        env_file='.env',
        secrets_configs=['secrets.json'],
        license='EULA',  # =(
        is_token_required=True,
    ),
    AddonModule(
        name='Metric',
        repo=GitLabRepo(
            url='https://dev.saltbox.pro/saltbox/saltbox-metric-compose',
            token=TOKEN,
        ),
        base_dir='saltbox-metric-compose',
        switchable_image_tags=['METRIC_IMAGE_TAG'],
        compose_files=['compose.yaml'],
        env_file='.env',
        license='EULA',  # =(
        is_token_required=True,
    ),
    AddonModule(
        name='Scheduler',
        repo=GitLabRepo(
            url='https://dev.saltbox.pro/saltbox/saltbox-scheduler-compose',
            token=TOKEN,
        ),
        base_dir='saltbox-scheduler-compose',
        switchable_image_tags=['SCHEDULER_IMAGE_TAG'],
        compose_files=['compose.yaml'],
        env_file='.env',
        secrets_configs=['secrets.json'],
        license='EULA',  # =(
        is_token_required=True,
    ),
]


class ScriptConfigurator:
    METRIC_DOCKER_SOCK_VAR='METRIC_DOCKER_SOCKET'
    METRIC_DOCKER_CONT_VAR='METRIC_DOCKER_CONTAINERS_PATH'
    DEFAULT_DOCKER_HOST='unix:///var/run/docker.sock'

    def __init__(self, args: argparse.Namespace, interactions: Interactions) -> None:
        self.args = args
        self.interactions = interactions
        self.conf = Config(force_host_as_name=args.host_is_name)
        self.cmd: List[str] = ['./install_saltbox.py']

    def _metric_docker_hook(self) -> None:
        addon_nama = 'Metric'
        if addon_nama not in {a.name for a in self.conf.selected_addons}:
            return

        dckr_host_cmd = ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}']
        dckr_host = os.environ.get('DOCKER_HOST')
        proc = subprocess.run(dckr_host_cmd, check=True, capture_output=True, text=True)
        dckr_host = proc.stdout.strip()
        if dckr_host== self.DEFAULT_DOCKER_HOST:
            print_out('Docker uses default socket', verbose=True)
            return
        dckr_host_parsed = urllib.parse.urlparse(proc.stdout.strip())
        if dckr_host_parsed.scheme != 'unix':
            dosa = (
                f'Docker uses `{dckr_host_parsed.scheme}` to connect the socket, '
                f'but Salt.Box {addon_nama} Compose supports `unix` only (file socket)')
            raise InstallerError(dosa)
        dckr_sock_path = dckr_host_parsed.path

        dckr_root_cmd = ['docker', 'info', '--format', '{{ .DockerRootDir }}']
        proc = subprocess.run(dckr_root_cmd, check=True, capture_output=True, text=True)
        dckr_root_path = proc.stdout.strip()
        dckr_cont_path = Path(dckr_root_path) / 'containers'
        print_out(
            '',
            f'Follwing Docker config detected and will be applied to Salt.Box {addon_nama} config:',
            INDENT + f'Socket path: `{dckr_sock_path}`',
            INDENT + f'Containers path: `{dckr_cont_path}`',
        )
        if self.interactions.ask_confirm('Continue with detected options?'):
            self.conf.extra_override = [
                f"{self.METRIC_DOCKER_SOCK_VAR}='{dckr_sock_path}'",
                f"{self.METRIC_DOCKER_CONT_VAR}='{dckr_cont_path}'",
                *self.conf.extra_override,
            ]
        else:
            raise InstallerError('Cancelled by user')

    def configure(self) -> Config:
        if self.args.addons:
            self.conf.selected_addons = ADDON_MODULES.copy()
            for addon in self.conf.selected_addons:
                addon.ref = self.conf.compose_ref

        if not self.args.non_interactive:
            self.cmd.append('--non-interactive')
        self.cmd += sys.argv[1:]

        if self.args.host is not None:
            self.conf.host = self.args.host
        else:
            self.conf.host = self.interactions.ask('Real address or name', self.conf.host)
            self.cmd += ['--host', self.conf.host]

        if self.args.port is not None:
            self.conf.port = self.args.port
        else:
            self.conf.port = self.interactions.ask_int('Port to serve HTTPS', self.conf.port)
            self.cmd += ['--port', str(self.conf.port)]

        if self.args.compose_ref is not None:
            self.conf.compose_ref = self.args.compose_ref
        else:
            self.conf.compose_ref = self.interactions.ask('Salt.Box Compose reference', self.conf.compose_ref)
            self.cmd += ['--compose-ref', self.conf.compose_ref]

        if self.conf.compose_ref not in Config.SUPPORTED_REFS:
            supported_refs = ', '.join(Config.SUPPORTED_REFS)
            print_out(
                '',
                f'Supported Compose references are: {supported_refs}, but '
                f'reference `{self.conf.compose_ref}` is selected. ')
            if not self.interactions.ask_confirm('Continue as advanced user?'):
                raise InstallerError('Cancelled by user')

        self.conf.compose_ref = resolve_ref(ref=self.conf.compose_ref, repo=COMPOSE_REPO)

        if self.args.admin is not None:
            self.conf.admin_name = self.args.admin
        else:
            self.conf.admin_name = self.interactions.ask(
                'Salt.Box Administrator\'s login', self.conf.admin_name)
            self.cmd += ['--admin', self.conf.admin_name]

        if not any(x.startswith(f'{ADMIN_SECRET_NAME}=') for x in self.args.explicit_secret):
            admin_pass = self.interactions.ask_optional(
                'Salt.Box Administartor\'s password (leave empty to generate)')
            if admin_pass is not None:
                admin_secret=f'{ADMIN_SECRET_NAME}={admin_pass}'
                self.args.explicit_secret.append(admin_secret)
                self.cmd += ['--explicit-secret', admin_secret]

        if not self.args.keep_addon_tags and self.conf.compose_ref in {Config.STABLE_BRANCH, Config.DEV_BRANCH}:
            msg = f'Select tag `{self.args.compose_ref}` for add-on modules?'
            if self.interactions.ask_confirm(msg):
                for addon in self.conf.selected_addons:
                    addon.ref = self.args.compose_ref
            else:
                self.cmd.append('--keep-addon-tags')
        if not self.args.keep_image_tags and self.conf.compose_ref == Config.DEV_BRANCH:
            self.conf.set_image_tags = self.interactions.ask_confirm(
                f'Select tag `{self.args.compose_ref}` for main images?')
            if not self.conf.set_image_tags:
                self.cmd.append('--keep-image-tags')

        self._metric_docker_hook()

        if not self.args.cleanup:
            self.conf.cleanup = self.interactions.ask_confirm(
                'Cleanup possibly existing instance? (Recommended, DATA LOST!)',
                default=False)
            if self.conf.cleanup:
                self.cmd.append('--cleanup')
            print_out('')
        else:
            self.conf.cleanup = self.args.cleanup

        try:
            self.conf.validate()
        except ValueError as err:
            raise InstallerError(err) from err

        print_out(
            'Selected options:',
            textwrap.indent(str(self.conf), INDENT),
            '',
        )

        cmd_str = ' '.join(self.cmd)
        print_out(
            'Command to repeat with no dialog:',
            '',
            INDENT + f'$ {cmd_str}',
            '',
        )

        if not self.interactions.ask_confirm('Continue?'):
            raise InstallerError('Cancelled by user')
        else:
            print_out('')

        if self.conf.is_token_required:
            print_out(f'Secret `{TOKEN_NAME}` will be saved by Docker for the registry!')
            if not self.interactions.ask_confirm('Continue?'):
                raise InstallerError('Cancelled by user')
            else:
                print_out('')

        print_out(
            30 * '#',
            '###  QUESTIONS ARE END NOW ###',
            30 * '#',
            ''
        )
        return self.conf

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

    docker_cmd = ['docker', 'version', '--format', '{{ .Server.Version }}']
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
    COMPOSE_REPO.download_ref(ref=config.compose_ref, output_dir=LOCAL_PATH)
    print_out()

    glob_iters = [BIN_DIR.glob(ptrn) for ptrn in SCRIPT_SUFFIXES]
    print_out('Making scripts executable:')
    for script in itertools.chain(*glob_iters):
        print_out(f'  - {script}')
        script.chmod(0o755)
    print_out()

    for addon in config.selected_addons:
        ref = resolve_ref(ref=addon.ref, repo=addon.repo)
        print_out(f'Downloading Salt.Box add-on module {addon.name} reference `{ref}`')
        print_out(f'URL: {addon.repo.url_for_ref(ref)}', verbose=True)
        addon.repo.download_ref(ref=ref, output_dir=Path(addon.base_dir))
        print_out()


def _configure_system_addons(config: Config) -> List[str]:
    override = []
    env_files = []
    secr_confs = []
    for addon in config.selected_addons:
        addon_dir = Path('..') / addon.base_dir
        override += [
            f'COMPOSE_FILE="${{COMPOSE_FILE}}:{addon_dir / cmp_f}"'
            for cmp_f in addon.compose_files
        ]
        env_files.append(f'{addon_dir / addon.env_file}')
        secr_confs += [f'{addon_dir / scr_conf}' for scr_conf in addon.secrets_configs]

    if env_files:
        val = ','.join(env_files)
        override.append(f"_UPDATE_AND_RUN_EXTRA_ENV_FILES='{val}'")
    if secr_confs:
        val = ','.join(secr_confs)
        override.append(f"_UPDATE_AND_RUN_EXTRA_SECRETS_CONFS='{val}'")

    return override


def configure_system(config: Config) -> None:
    override = []

    if config.set_image_tags:
        for tag_var in SWITCHABLE_IMAGE_TAGS:
            override.append(f"{tag_var}='{config.compose_ref}'")
        for addon in config.selected_addons:
            override.extend(
                f"{tag_var}='{config.compose_ref}'"
                for tag_var in addon.switchable_image_tags)

    override.extend([
        f"SALTBOX_ADMIN_USERNAME='{config.admin_name}'",
        f"WEB_SERVER_OUTER_SOCKET='{config.host}:{config.port}'"
    ])
    if config.is_host_seems_ip and not config.force_host_as_name:
        override.append(f"WEB_SERVER_SSL_ALT_NAMES_IP='127.0.0.1,{config.host}'")
    else:
        override.append(f"WEB_SERVER_SSL_ALT_NAMES_DNS='localhost,{config.host}'")

    override.extend(_configure_system_addons(config=config))

    override.extend(config.extra_override)

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

    if config.is_token_required:
        run_cmd([*ENTRYPOINT, '--only-env'])
        registry = get_dotenv_var(name = REGISTRY_DOTENV_VAR, dotenv=Path('.env'))
        if not registry:
            dosa = f'Failed to obtain `{REGISTRY_DOTENV_VAR}`'
            raise InstallerError(dosa)
        docker_srv = Path(registry).parts[0]
        cmd = ['docker', 'login', '--username', config.registry_user, '--password-stdin', docker_srv]
        run_cmd(cmd=cmd, input=TOKEN)

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
        check(args=args)
        conf = ScriptConfigurator(args=args, interactions=interactions).configure()
        download(args=args, config=conf)
        configure_system(config=conf)
        with cd(LOCAL_PATH):
            run(args, config=conf)
    except InstallerError as papa:
        print_err('', papa, '', 'Exit on error', '')
        sys.exit(1)


if __name__ == '__main__':
    main()
