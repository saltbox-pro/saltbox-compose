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

Script should works standalone. No Python modules required. Run in an empty directory.

Requires python>=3.7.3
"""

# TODO (a.karmanov): Offline mode with images

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
from typing import Any, ClassVar, Dict, List, NoReturn, Optional, Sequence, TextIO, Type, TypeVar, Union

ENC = 'UTF-8'
INDENT = 2 * ' '
HTTP_CHUNK_BYTE = 8192
HTTP_TIMEOUT_SEC = 30
VERSION_TAG_PATTERN = re.compile(r'^v\d+\.\d+\.\d+.*$')  # v0.1.1-ANY
RELEASE_ONLY_TAG_PATTERN = re.compile(r'^v\d+\.\d+\.\d+$')  # v0.1.1.
CWD = Path.cwd()
LOCAL_PATH = CWD / './saltbox-compose/'
BIN_DIR = LOCAL_PATH / 'bin'
DOTENV_TOOL_PATH = BIN_DIR / 'dotenv_tool.sh'
ENV_OVERRIDE = LOCAL_PATH / 'override.env'
DEFAULT_DOTENVS = (LOCAL_PATH / 'base.env', ENV_OVERRIDE,)
SCRIPT_SUFFIXES = ('*.sh', '*.py',)
ADMIN_SECRET_NAME = 'saltbox_admin_password'
MONGO_ADMIN_SECRET_NAME = 'mongo_root_password'
RELEASE_REF = 'RELEASE'
PRERELEASE_REF = 'PRERELEASE'
REGISTRY_DOTENV_VAR = 'IMAGE_REGISTRY'
INSTALLER_METADATA_FILE = '.installer.json'
SCRIPT_NAME = 'install_saltbox.py'

_CACHE_HOME = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
CACHE_DIR = _CACHE_HOME / 'install_saltbox'

# Uses after changind CWD
PREMAKE_SECRETS_CMD = ['bin/make_secrets.py']
ENTRYPOINT = ['bin/update_and_run.sh', '--no-root', '--force', '--detach', '--no-git-pull']

SALTBOX_COMPOSE_REQUIRED_COMPATIBILITY_LEVEL = 2
MIN_DOCKER_VERSION = '25.0.0'
MIN_COMPOSE_VERSION = '2.20.2'
MIN_PYTHON_VERSION = '3.7.3'

cache = functools.lru_cache(maxsize=None)

TOKEN_NAME = 'SALTBOX_INSTALL_TOKEN'
# GitLab group token MUST have scopes: read_repository, read_registry, read_api
TOKEN = os.environ.get(TOKEN_NAME)
# CI_JOB_TOKEN must be passed as 'JOB-TOKEN' header
TOKEN_HEADER = os.environ.get('SALTBOX_INSTALL_TOKEN_HEADER', 'PRIVATE-TOKEN')


class InstallerError(RuntimeError):
    def __init__(self, message: Union[str, BaseException], details: Optional[str] = None) -> None:
        super().__init__(message)
        self.details = details


class CheckError(InstallerError): ...
class ConfigError(InstallerError): ...  # noqa: E302
class HttpNotFoundError(InstallerError): ...  # noqa: E302


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
        '--list-addons',
        action='store_true',
        help='List addons in JSON format and exit',
    )
    parser.add_argument(
        '--addons',
        action='append',
        default=None,
        help=(
            f'Install also official Salt.Box Addons: {ADDONS_SEL_STR}. '
            '`FREE` by default. '
            'SOME ADDONS ARE PROPRIETARY, TOKEN REQUIRED. '  # =(
            'Can be specified multiple times.'
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
            'Salt.Box Compose Git reference to obtain. '
            f'`{RELEASE_REF}` for latest release, '
            f'`{PRERELEASE_REF}` for latest release OR pre-release '
            '(what is the latest). '
            f'`{Config.DEV_BRANCH}` for the same name branch. '
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
        '--git',
        action='store_true',
        help='Clone Git repositories instead of downloading archives'
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
    parser.add_argument(
        '-n', '--non-interactive',
        action='store_true',
        help='Do not ask to input, use defaults',
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Remove previously downloaded archives of repositories',
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
        help='Prepare but do not run',
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print more info',
    )
    return parser.parse_args()


VERBOSE = False


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


def run_cmd(
    cmd: List[str],
    input: Optional[str] = None,
    extra_env: Optional[Dict[str, str]] = None,
    skip: bool = False,
) -> None:
    env = os.environ.copy()
    if extra_env is not None:
        env.update(extra_env)
    cmd_str = ' '.join(cmd)
    if skip:
        print_out(f'Skipping Run `{cmd_str}`', '')
        return
    else:
        print_out(f'Running `{cmd_str}`', '')
    try:
        subprocess.run(cmd, env=env, input=input, check=True, text=True)
    except subprocess.CalledProcessError as err:
        raise InstallerError(err) from None


def _print(*args, file: TextIO, verbose: bool = False) -> None:
    if verbose and not VERBOSE:
        return
    print(*args, file=file, sep='\n')


def print_out(*args, verbose: bool = False) -> None:
    _print(*args, verbose=verbose, file=sys.stdout)


def print_err(*args, verbose: bool = False) -> None:
    _print(*args, verbose=verbose, file=sys.stderr)


@dataclasses.dataclass
class InsallerMetadata:
    compatibility_level: int


def get_installer_meta(repo_path: Path) -> Optional[InsallerMetadata]:
    meta_full_path = repo_path / INSTALLER_METADATA_FILE
    dir_name = repo_path.name
    if not meta_full_path.exists():
        print_err('', f'No installer metadata file `{INSTALLER_METADATA_FILE}` in {dir_name}', '')
        return None
    with meta_full_path.open('r') as f:
        data = json.load(f)
    try:
        return InsallerMetadata(**data)
    except TypeError as err:
        dtls = (
            f'Repository `{dir_name}` contains unexpectedly formatted\n'
            'Installer metadata file. Please report to support or try another\n'
            f'{SCRIPT_NAME} or Salt.Box Compose version.'
        )
        raise InstallerError(err, details=dtls)


def check_repo_compability_level(repo_path: Path, required_level: Optional[int]) -> None:
    if required_level is None:
        return
    meta = get_installer_meta(repo_path)
    cmp_lvl = meta.compatibility_level if meta else None
    if cmp_lvl is None or cmp_lvl < required_level:
        dir_name = repo_path.name
        cmp_str = str(cmp_lvl) if cmp_lvl is not None else 'unspecified'
        msg = f'Repository `{dir_name}` seems incompatible with this `{SCRIPT_NAME}` version'
        details = (
            f'The script requires compability level {required_level} for `{dir_name}`, but\n'
            f'repository level is {cmp_str}. Please try another `--compose-ref` value\n'
            'or contact support.'
        )
        raise CheckError(message=msg, details=details)


def get_dotenv_var(name: str) -> str:
    """ Read str value from dotenv files """
    cmd = ['bash', str(DOTENV_TOOL_PATH), 'get', name]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    val = proc.stdout
    if val.endswith('\n'):
        val = val[:-1]
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

    def ask_choices(
        self,
        prompt: str,
        choices: Sequence[str],
        default: Optional[str] = None,
    ) -> str:
        if not choices:
            dosa = 'No choices for prompt'
            raise InstallerError(dosa)
        choices_s = set(choices)
        if default is not None and default not in choices_s:
            dosa = f'Incorrect default `{default}`'
            raise InstallerError(dosa)
        prompt = f'prompt {choices_s}'
        while True:
            val = self.ask(prompt=prompt, default=default)
            if val in choices_s:
                return val
            print_err(f'`{val}` not in {choices_s}')

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
            resp = input(prompt).strip().lower()
            if not resp:
                return default
            elif resp in ('y', 'yes',):
                return True
            elif resp in ('n', 'no',):
                return False
            print_err('Unexpected input')


@dataclasses.dataclass
class Config:
    MIN_PORT: ClassVar = 1
    MAX_PORT: ClassVar = 2**16 - 1
    HOSTNAME_LABEL_PATTERN: ClassVar = re.compile(r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$')

    DEV_BRANCH: ClassVar = 'dev'
    SUPPORTED_REFS: ClassVar = [RELEASE_REF, PRERELEASE_REF, DEV_BRANCH]

    # Non-default args mostly are interactive-agnostic

    # Use Git rather than pure HTTP
    git_clone: bool
    # Do not show any dynamic progress
    no_progress: bool
    # Prepare but do not start
    skip_run: bool
    explicit_secrets: List[str]

    # Default args mostly are interactive-related

    cleanup: bool = False
    host: str = 'saltbox.local'
    port: int = 443
    compose_ref: str = RELEASE_REF
    force_host_as_name: bool = False
    admin_name: str = 'master'
    extra_override: List['str'] = dataclasses.field(default_factory=list)
    selected_addons: List['AddonModule'] = dataclasses.field(default_factory=list)
    registry_user: str = 'install_saltbox'
    # Migrations is a special module with totally independent Compose project.
    # Field value means install corresponding ref of `saltbox-migration-compose`.
    # `None` to not install Salt.Box Migrations
    migrations_ref: Optional[str] = None

    def validate(self) -> None:
        if not self.MIN_PORT <= self.port <= self.MAX_PORT:
            dosa = f'Port {self.port} is out of range {self.MIN_PORT}-{self.MAX_PORT}'
            raise ConfigError(dosa)
        self._validate_host()
        if TOKEN is None and self.is_token_required:
            dosa = f'Missing required `{TOKEN_NAME}` env variable'
            dtls = (
                'Some selected addons depends on private repositories. To gain\n'
                'access please request token from vendor, than export it as an\n'
                'environment variable:\n'
                f"{INDENT}$ export {TOKEN_NAME}='YOUR_TOKEN'\n\n"
                'Or pass it before an install command (more secure):\n'
                f"{INDENT}$ {TOKEN_NAME}='YOUR_TOKEN' ./{SCRIPT_NAME} ..."
            )
            raise ConfigError(message=dosa, details=dtls)

    @property
    def outer_socket(self) -> str:
        return f'{self.host}:{self.port}'

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
            raise ConfigError('Too long DNS name')
        elif not self.host:
            raise ConfigError('Empty hostname')
        if not self.compose_ref:
            raise ConfigError('Empty compose_ref')
        for part in self.host.split('.'):
            if not self.HOSTNAME_LABEL_PATTERN.match(part):
                dosa = f'Hostname part `{part}` seems not valid'
                raise ConfigError(dosa)

    def __str__(self) -> str:
        data = [f'Serve on: `{self.host}:{self.port}`']
        if self.is_host_seems_ip:
            wut = 'a DNS name' if self.force_host_as_name else 'an IP address'
            data[0] += f' (Host part is treated as {wut})'
        data.append(f'Salt.Box Compose reference is: `{self.compose_ref}`')
        data.append(f'Salt.Box Administrator\'s login is: `{self.admin_name}`')
        data.append('Salt.Box Administrator\'s password is: [ SEARCH IN FURTHER OUTPUT ]')
        if self.selected_addons:
            addons_spec_list = [f'  - {a.name} (license: `{a.license}`, ref: `{a.ref}`)' for a in self.selected_addons]
            if self.migrations_ref:
                mig_str = f'  - {_MIGRATIONS_NAME} (license: `{_MIGRATIONS_LICENSE}`, ref: `{self.migrations_ref}`)'
                addons_spec_list.append(mig_str)
            addons_str = '\n'.join(addons_spec_list)
            data.append(f'Add-on modules:\n{addons_str}')
        data.append(f'Cleanup: {"YES!!! " if self.cleanup else "no"}')
        return '\n'.join(data)


VersionSelf = TypeVar('VersionSelf', bound='Version')


class Version:
    """ Represents simplified SemVer"""
    # Simplified official regex (https://regex101.com/r/Ly7O1x/3)
    # at https://regex101.com/r/Ly7O1x/3225
    PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.'
        r'(?P<minor>0|[1-9]\d*)\.'
        r'(?P<patch>0|[1-9]\d*)'
        # Some distros uses non-standard version strings like '28.3.3.astra1'
        r'(\.(?P<special>.*))?'
        r'(-(?P<pre_release>[\.a-zA-Z0-9-]*))?'
        r'(\+(?P<build>[\.a-zA-Z0-9-]*))?$'
    )

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        pre_release: Optional[str] = None,
        build: Optional[str] = None,
    ) -> None:
        self._version = (major, minor, patch,)
        self.pre_release = pre_release
        self.build = build
        self.special: Optional[str] = None

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
            pre_release=match.group('pre_release'),
            build=match.group('build'),
        )
        obj.special = match.group('special')
        return obj

    def __str__(self) -> str:
        result = f'{self.major}.{self.minor}.{self.patch}'
        if self.special is not None:
            result += f'.{self.special}'
        if self.pre_release is not None:
            result += f'-{self.pre_release}'
        if self.build is not None:
            result += f'+{self.build}'
        return result

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self._version == self._version
            and
            self.pre_release == self.pre_release
        )

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        for i in range(len(self._version)):
            if self._version[i] < other._version[i]:
                return True
            elif self._version[i] > other._version[i]:
                return False

        # Pre-release version has lower precedence than a regular version
        if self.pre_release == other.pre_release:
            return False

        if self.pre_release is None or other.pre_release is None:
            return other.pre_release is None
        else:
            return self.pre_release < other.pre_release


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
    MAX_CONENT_LEN_PRINT = 2000

    def __init__(self, url: str, token: Optional[str] = None) -> None:
        self.token = token
        url_obj = urllib.parse.urlparse(url)
        path = Path(url_obj.path)
        self.scheme = url_obj.scheme
        self.server = url_obj.netloc
        self.owner = str(path.parent).lstrip('/')
        self.project = path.name

    @property
    def api_url(self) -> str:
        return f'{self.scheme}://{self.server}/api/v4'

    @property
    def api_project_url(self) -> str:
        return f'{self.api_url}/projects/{self.owner}%2F{self.project}'

    @cache
    def get_registry_repositories(self, tags: bool = False) -> Any:
        # NOTE Paginated response has 100 max results witch is enough for
        # Salt.Box project as for now
        tags_val = json.dumps(tags)
        params = urllib.parse.urlencode({'tags': tags_val, 'per_page': '100'})
        url = f'{self.api_project_url}/registry/repositories?{params}'
        try:
            resp = urllib.request.urlopen(url=self._create_request(url=url))
        except urllib.error.URLError as papa:
            dosa = f'Error on requesting URL {url}: {papa}'
            raise InstallerError(dosa) from None
        body = json.load(resp)
        return body

    @cache
    def get_tags(self) -> List[str]:
        """ Get list of tags sorted by commit date """
        params = urllib.parse.urlencode({'order_by': 'updated', 'sort': 'asc'})  # Ordered by commit date
        url = f'{self.api_project_url}/repository/tags?{params}'
        try:
            resp = urllib.request.urlopen(url=self._create_request(url=url))
        except urllib.error.URLError as papa:
            dosa = f'Error on requesting URL {url}: {papa}'
            raise InstallerError(dosa) from None
        body = json.load(resp)
        return [i['name'] for i in body]

    def get_version_tags(self, allow_pre_releases=False) -> List[str]:
        """ Get list of latest tags sorted by commit date """
        regex = VERSION_TAG_PATTERN if allow_pre_releases else RELEASE_ONLY_TAG_PATTERN
        versions = list(filter(lambda x: regex.match(x), self.get_tags()))
        ver_objs = [Version.from_str(v.lstrip('v')) for v in versions]
        versions = [f'v{ver}' for ver in sorted(ver_objs)]
        return versions

    def get_latest_version_tag(self, allow_pre_releases=False) -> str:
        tags = self.get_version_tags(allow_pre_releases=allow_pre_releases)
        assert len(tags) > 0, 'Found no tags in saltbox-compose repository'
        return tags[-1]

    @cache
    def normalize_ref(self, ref: str) -> str:
        """ Resolve special values to regular ref """
        if ref == RELEASE_REF:
            return self.get_latest_version_tag(allow_pre_releases=False)
        if ref == PRERELEASE_REF:
            return self.get_latest_version_tag(allow_pre_releases=True)
        return ref

    @cache
    def resolve_ref_to_sha(self, ref: str) -> str:
        """ Resolve Ref inlcuding special values to commit SHA """
        ref = self.normalize_ref(ref)
        url = f'{self.api_project_url}/repository/commits/{ref}'
        try:
            resp = urllib.request.urlopen(url=self._create_request(url=url))
        except urllib.error.URLError as papa:
            dosa = f'Error on requesting URL {url}: {papa}'
            raise InstallerError(dosa) from None
        body = json.load(resp)
        return body['id']

    def url_for_ref(self, ref: str) -> str:
        params = urllib.parse.urlencode({'sha': ref})
        return (
            f'{self.api_url}/projects/{self.owner}%2F{self.project}/repository/'
            f'archive.{self.ARCHIVE_SUFFIX}?{params}'
        )

    @property
    def git_url(self) -> str:
        auth = ''
        if self.token is not None:
            auth = f'token:{self.token}@'
        return f'{self.scheme}://{auth}{self.server}/{self.owner}/{self.project}.git'

    def obtain_ref(self, use_git: bool, ref: str, output_dir: Path, progress: bool = True) -> None:
        """
        Get repository

        :raises HttpNotFoundError: on 404
        :raises InstallerError: on HTTP or network errors
        """
        if use_git:
            fun = self.git_clone_ref
        else:
            fun = self.download_ref
        fun(ref=ref, output_dir=output_dir, progress=progress)

    def git_clone_ref(self, ref: str, output_dir: Path, progress: bool = True) -> None:
        """
        Get Git repository and switch it to ref

        :raises InstallerError: on HTTP or network errors
        """
        repo_dir = str(output_dir)
        ref = self.normalize_ref(ref)
        commands = [
            ['git', 'clone', '--no-checkout', '--depth=1', self.git_url, repo_dir],
            ['git', '-C', repo_dir, 'fetch', '--depth=1', 'origin', ref],
            ['git', '-C', repo_dir, 'checkout', 'FETCH_HEAD'],
        ]
        if not progress:
            for cmd in commands:
                cmd.append('--quiet')
        for cmd in commands:
            run_cmd(cmd=cmd)

    def download_ref(self, ref: str, output_dir: Path, progress: bool = True) -> None:
        """
        Get code of ref version with no Git

        :raises HttpNotFoundError: on 404
        :raises InstallerError: on HTTP or network errors
        """
        if output_dir.exists():
            dosa = f'Already exists: `{output_dir}`'
            raise InstallerError(dosa)

        ref = self.resolve_ref_to_sha(ref)
        arch_path = CACHE_DIR / f'{self.project}-{ref}.{self.ARCHIVE_SUFFIX}'

        if not arch_path.exists():
            url = self.url_for_ref(ref)
            request = self._create_request(url=url)
            try:
                download_file(request=request, output=arch_path, progress=progress)
            except HttpNotFoundError:
                dosa = f'Server returns `Not found` for Compose ref `{ref}`'
                raise InstallerError(dosa) from None
            if not zipfile.is_zipfile(arch_path):
                data = arch_path.read_text(encoding=ENC)
                if len(data) > self.MAX_CONENT_LEN_PRINT:
                    data = data[:self.MAX_CONENT_LEN_PRINT] + '...'
                dosa = f'Downloaded code archive is not a {self.ARCHIVE_SUFFIX} file'
                details = f'Content of `{arch_path}`:\n' + data
                raise InstallerError(dosa, details=details)
        else:
            print_out(f'Unpacking `{arch_path.name}` from cache')

        arch = zipfile.ZipFile(arch_path)
        dir_name = arch.namelist()[0]
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_path = Path(tmp_dir_name)
            arch.extractall(path=tmp_path)
            shutil.move(src=str(tmp_path / dir_name), dst=output_dir)

    def _create_request(self, url: str) -> urllib.request.Request:
        request = urllib.request.Request(url=url)
        if self.token:
            request.headers[TOKEN_HEADER] = self.token
        return request


COMPOSE_REPO = GitLabRepo(url='https://dev.saltbox.pro/saltbox/saltbox-compose')


@dataclasses.dataclass
class AddonModule:
    name: str
    url: str
    repo: GitLabRepo = dataclasses.field(init=False)
    base_dir: str
    license: str
    env_file: str
    is_token_required: bool
    ref: str = RELEASE_REF
    # Compare to a value from a special file in the repository
    required_compatibility_level: Optional[int] = None

    def __post_init__(self) -> None:
        kwargs: Dict[str, Any] = {'url': self.url}
        if self.is_token_required:
            kwargs['token'] = TOKEN
        self.repo = GitLabRepo(**kwargs)


ADDONS_MODULES = [
    AddonModule(
        name='FileBrowser',
        url='https://dev.saltbox.pro/saltbox/saltbox-filebrowser-compose',
        base_dir='saltbox-filebrowser-compose',
        env_file='.env',
        license='Apache-2.0',
        is_token_required=False,
        required_compatibility_level=1,
    ),
    AddonModule(
        name='Inventory',
        url='https://dev.saltbox.pro/saltbox/saltbox-inventory-compose',
        base_dir='saltbox-inventory-compose',
        env_file='.env',
        license='EULA',  # =(
        is_token_required=True,
        required_compatibility_level=1,
    ),
    AddonModule(
        name='Metric',
        url='https://dev.saltbox.pro/saltbox/saltbox-metric-compose',
        base_dir='saltbox-metric-compose',
        env_file='.env',
        license='Apache-2.0',
        is_token_required=False,
        required_compatibility_level=1,
    ),
    AddonModule(
        name='Scheduler',
        url='https://dev.saltbox.pro/saltbox/saltbox-scheduler-compose',
        base_dir='saltbox-scheduler-compose',
        env_file='.env',
        license='EULA',  # =(
        is_token_required=True,
        required_compatibility_level=1,
    ),
    AddonModule(
        name='ClientToolkit',
        url='https://dev.saltbox.pro/saltbox/saltbox-client-toolkit-compose',
        base_dir='saltbox-client-toolkit-compose',
        env_file='.env',
        license='EULA',  # =(
        is_token_required=True,
        required_compatibility_level=1,
    ),
]
ADDONS_MAPPING = {a.name: a for a in ADDONS_MODULES}
_MIGRATIONS_NAME = 'Migrations'
_MIGRATIONS_LICENSE = 'EULA'
_INSTALL_MIGRATIONS_BIN = BIN_DIR / 'install_saltbox_migrations.py'
ADDONS_SELECTOR = {
    **{i: [i] for i in ADDONS_MAPPING},
     _MIGRATIONS_NAME: [_MIGRATIONS_NAME],
    'FREE': [i.name for i in ADDONS_MAPPING.values() if i.license != 'EULA'],
    'ALL': [*ADDONS_MAPPING.keys(), _MIGRATIONS_NAME],
    'NONE': [],
}
ADDONS_SEL_STR = ", ".join(f'`{i}`' for i in ADDONS_SELECTOR)


class ScriptConfigurator:
    METRIC_DOCKER_SOCK_VAR = 'METRIC_DOCKER_SOCKET'
    METRIC_DOCKER_CONT_VAR = 'METRIC_DOCKER_CONTAINERS_PATH'
    DEFAULT_DOCKER_HOST = 'unix:///var/run/docker.sock'

    def __init__(self, args: argparse.Namespace, interactions: Interactions) -> None:
        self.args = args
        self.interactions = interactions
        self.conf = Config(
            git_clone=args.git,
            no_progress=args.no_progress,
            skip_run=args.skip_run,
            explicit_secrets=args.explicit_secret.copy(),
            force_host_as_name=args.host_is_name,
            extra_override=args.OVERRIDE.copy()
        )
        self.cmd: List[str] = [f'./{SCRIPT_NAME}']

    def _metric_docker_hook(self) -> None:
        addon_nama = 'Metric'
        if addon_nama not in {a.name for a in self.conf.selected_addons}:
            return

        dckr_host_cmd = ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}']
        dckr_host = os.environ.get('DOCKER_HOST')
        proc = subprocess.run(dckr_host_cmd, check=True, capture_output=True, text=True)
        dckr_host = proc.stdout.strip()
        if dckr_host == self.DEFAULT_DOCKER_HOST:
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
        sys.stdout.flush()
        if self.interactions.ask_confirm('Continue with detected options?'):
            self.conf.extra_override = [
                f"{self.METRIC_DOCKER_SOCK_VAR}='{dckr_sock_path}'",
                f"{self.METRIC_DOCKER_CONT_VAR}='{dckr_cont_path}'",
                *self.conf.extra_override,
            ]
        else:
            raise InstallerError('Cancelled by user')

    def _select_addons(self) -> None:
        # TODO (a.karmanov): Interactive select
        if self.args.addons is None:
            self.conf.selected_addons = [ADDONS_MAPPING[i] for i in ADDONS_SELECTOR['FREE']]
        else:
            try:
                selected_addons_names = list({name for sel in self.args.addons for name in ADDONS_SELECTOR[sel]})
            except KeyError as err:
                bad_name = str(err).strip("'")
                dosa = f'Unknown addon name `{bad_name}`'
                dtls = (
                    f'Allowed values for `--addons` are: {ADDONS_SEL_STR}\n'
                    'Flag can be specified multiple times.'
                )
                raise InstallerError(message=dosa, details=dtls)
            if _MIGRATIONS_NAME in selected_addons_names:
                selected_addons_names.remove(_MIGRATIONS_NAME)
                self.conf.migrations_ref = RELEASE_REF
            self.conf.selected_addons = [ADDONS_MAPPING[i] for i in selected_addons_names]
            for addon in self.conf.selected_addons:
                addon.ref = self.conf.compose_ref
        # Early TOKEN for private Addons check
        self.conf.validate()

    def _migrations_ref_hook(self) -> None:
        if self.conf.migrations_ref is not None:
            self.conf.migrations_ref = self.conf.compose_ref

    def configure(self) -> Config:
        self._select_addons()

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
            self.conf.compose_ref = self.interactions.ask_choices(
                'Salt.Box Compose reference',
                default=self.conf.compose_ref,
                choices=Config.SUPPORTED_REFS)
            self.cmd += ['--compose-ref', self.conf.compose_ref]

        self._migrations_ref_hook()

        if self.args.admin is not None:
            self.conf.admin_name = self.args.admin
        else:
            self.conf.admin_name = self.interactions.ask(
                'Salt.Box Administrator\'s login', self.conf.admin_name)
            self.cmd += ['--admin', self.conf.admin_name]

        if not any(x.startswith(f'{ADMIN_SECRET_NAME}=') for x in self.conf.explicit_secrets):
            admin_pass = self.interactions.ask_optional(
                'Salt.Box Administartor\'s password (leave empty to generate)')
            if admin_pass is not None:
                admin_secret = f'{ADMIN_SECRET_NAME}={admin_pass}'
                self.conf.explicit_secrets.append(admin_secret)
                self.cmd += ['--explicit-secret', admin_secret]

        for addon in self.conf.selected_addons:
            addon.ref = self.conf.compose_ref

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

        self.conf.validate()

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


class Checker:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    def _check_cwd(self) -> None:
        atta = Path(__file__).name
        content = {i.name for i in CWD.iterdir()}
        print_out('CWD content: ' + ', '.join(content), verbose=True)
        content -= {atta}
        if content:
            dosa = f'Current working directory contains files other than `{atta}`'
            details = (
                'Script creates one or more directories in the current working\n'
                'directory. This check ensures no 3rd part file in the CWD to\n'
                'avoid conflicts.\n\n'
                'Please decide to run the script in a clean directory or cleanup\n'
                'current directory manually to retry the installation process.'
            )
            raise CheckError(dosa, details=details)

    def _check_python(self) -> None:
        py_ver = Version(
            major=sys.version_info.major,
            minor=sys.version_info.minor,
            patch=sys.version_info.micro,
        )
        min_py_ver = Version.from_str(MIN_PYTHON_VERSION)
        print_out(f'Running on Python version `{py_ver}`')
        if py_ver < min_py_ver:
            raise CheckError(f'Minimal required Python version is v{MIN_PYTHON_VERSION}')

    def _check_git(self) -> None:
        if not self.args.git:
            return
        cmd = ['git', 'version']
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            dosa = 'Not found `git` command. Git is not installed?'
            raise CheckError(dosa) from None
        except OSError as err:
            raise CheckError(err) from None
        if proc.returncode != 0:
            dosa = f'Command `{" ".join(cmd)}` failed'
            dtl = 'Process stderr:\n' + proc.stderr
            raise CheckError(dosa, details=dtl)
        ver_str = proc.stdout.strip().split()[-1]
        print_out(f'Git version is `{ver_str}`')

    def _check_docker(self) -> None:
        docker_cmd = ['docker', 'version', '--format', '{{ .Server.Version }}']
        try:
            proc = subprocess.run(docker_cmd, capture_output=True, text=True)
        except FileNotFoundError:
            dosa = 'Not found `docker` command. Not installed or not in PATH?'
            raise CheckError(dosa) from None
        except OSError as err:
            raise CheckError(err) from None
        if proc.returncode != 0:
            dosa = f'Command `{" ".join(docker_cmd)}` failed. May be use `sudo` to run as root?'
            dtl = 'Process stderr:\n' + proc.stderr
            raise CheckError(dosa, details=dtl)
        docker_ver_str = proc.stdout.strip()
        print_out(f'Docker version string is `{docker_ver_str}`')
        docker_ver = Version.from_str(docker_ver_str)
        min_docker_ver = Version.from_str(MIN_DOCKER_VERSION)
        if docker_ver < min_docker_ver:
            raise CheckError(f'At least Docker v{MIN_DOCKER_VERSION} required')

    def _check_compose(self) -> None:
        compose_cmd = ['docker', 'compose', 'version', '--short']
        try:
            proc = subprocess.run(compose_cmd, capture_output=True, text=True)
        except OSError as err:
            raise CheckError(err) from None
        if proc.returncode != 0:
            dosa = f'Command `{" ".join(compose_cmd)}` failed. Is Docker Compose installed?'
            dtl = 'Process stderr:\n' + proc.stderr
            raise CheckError(dosa, details=dtl)
        compose_ver_str = proc.stdout.strip()
        compose_ver = Version.from_str(compose_ver_str)
        min_compose_ver = Version.from_str(MIN_COMPOSE_VERSION)
        if compose_ver < min_compose_ver:
            raise CheckError(f'At least Docker Compose v{MIN_COMPOSE_VERSION} required')
        print_out(f'Docker Compose version string is `{compose_ver_str}`')

    def _check_sys(self) -> None:
        try:
            val = Path('/proc/sys/vm/overcommit_memory').read_text(encoding=ENC).strip()
        except OSError as err:
            InstallerError(err)
        if val != '1':
            dosa = 'Improper `vm.overcommit_memory` value'
            dtls = (
                'Redis requires host system option `vm.overcommit_memory=1` (always overcommit).\n'
                'It can be done with the following commands:\n\n'
                f'{INDENT}# echo \'vm.overcommit_memory=1\' > /etc/sysctl.d/saltbox.conf\n'
                f'{INDENT}# sysctl vm.overcommit_memory=1'
            )
            raise CheckError(dosa, details=dtls)

    def _check_cpuinfo(self) -> None:
        cpuinfo_path = Path('/proc/cpuinfo/')
        flags = None
        with cpuinfo_path.open('r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    # First core data ended
                    break
                spl = [i.strip() for i in line.split(':', maxsplit=1)]
                if spl[0] == 'flags':  # Is OK for AMD64, but can be 'Features' for ARM
                    flags = spl[1].split()
                    break
        if flags is None:
            dosa = f'Not found `flags` field in `{cpuinfo_path}`'
            raise CheckError(dosa)
        print_out(f'Found CPU flags: {flags}', verbose=True)
        if 'avx' not in flags or 'avx2' not in flags:
            dosa = 'Missing required CPU flags'
            dtl = (
                'MongoDB depends on AVX, AVX2 CPU features.\n'
                'Please review CPU configuration of the host.')
            raise CheckError(message=dosa, details=dtl)

    def check(self) -> None:
        if self.args.skip_check:
            print_out('Skipping requirements checkup!', '')
            return
        self._check_cwd()
        self._check_python()
        self._check_git()
        self._check_docker()
        self._check_compose()
        self._check_cpuinfo()
        self._check_sys()
        print_out()


def download(config: Config) -> None:
    progress = not config.no_progress
    sha = COMPOSE_REPO.resolve_ref_to_sha(config.compose_ref)
    print_out(f'Downloading Salt.Box Compose reference `{config.compose_ref}` (SHA {sha})...')
    print_out(f'URL: {COMPOSE_REPO.url_for_ref(config.compose_ref)}', verbose=True)
    COMPOSE_REPO.obtain_ref(
        use_git=config.git_clone, ref=config.compose_ref, output_dir=LOCAL_PATH, progress=progress)
    check_repo_compability_level(
        repo_path=LOCAL_PATH,
        required_level=SALTBOX_COMPOSE_REQUIRED_COMPATIBILITY_LEVEL,
    )
    print_out()

    glob_iters = [BIN_DIR.glob(ptrn) for ptrn in SCRIPT_SUFFIXES]
    print_out('Making scripts executable:')
    for script in itertools.chain(*glob_iters):
        print_out(f'  - {script}')
        script.chmod(0o755)
    print_out()

    for addon in config.selected_addons:
        sha = addon.repo.resolve_ref_to_sha(addon.ref)
        print_out(f'Downloading Salt.Box add-on module {addon.name} reference `{addon.ref}` (SHA {sha})')
        print_out(f'URL: {addon.repo.url_for_ref(addon.ref)}', verbose=True)
        repo_path = Path(addon.base_dir)
        addon.repo.obtain_ref(
            use_git=config.git_clone, ref=addon.ref, output_dir=repo_path, progress=progress)
        check_repo_compability_level(
            repo_path=repo_path,
            required_level=addon.required_compatibility_level,
        )
        print_out()


def _configure_system_addons(config: Config) -> List[str]:
    override = []
    env_files = []
    for addon in config.selected_addons:
        addon_dir = Path('..') / addon.base_dir
        env_files.append(f'{addon_dir / addon.env_file}')
    if env_files:
        val = ','.join(env_files)
        override.append(f"_UPDATE_AND_RUN_EXTRA_ENV_FILES='{val}'")
    return override


def configure_system(config: Config) -> None:
    override = []

    override.extend([
        f"SALTBOX_ADMIN_USERNAME='{config.admin_name}'",
        f"WEB_SERVER_OUTER_SOCKET='{config.outer_socket}'"
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


def _deploy_migrations_hook(config: Config) -> None:
    if config.migrations_ref is None:
        return
    with Path(LOCAL_PATH / f'secrets/{MONGO_ADMIN_SECRET_NAME}').open('r') as f:
        mongo_secr = f.read()
    mig_dpl_cmd = [
        str(_INSTALL_MIGRATIONS_BIN),
        '--path', str(CWD),
        '--compose-ref', config.migrations_ref,
        '--saltbox-outer-socket', config.outer_socket,
        '--internal',
    ]
    if config.cleanup:
        mig_dpl_cmd.append('--cleanup')
    if config.git_clone:
        mig_dpl_cmd.append('--git')
    if config.no_progress:
        mig_dpl_cmd.append('--no-progress')
    if config.skip_run:
        print_out('Remember Salt.Box Migrations requires separate commands to cleanup and start!', '')
        mig_dpl_cmd.append('--skip-run')
    run_cmd(mig_dpl_cmd, extra_env={'MONGO_ADMIN_PASSWORD': mongo_secr})


def run(config: Config) -> None:
    ep_cmd = ENTRYPOINT.copy()
    if config.no_progress:
        ep_cmd.append('--no-progress')

    if config.is_token_required:
        registry = get_dotenv_var(name=REGISTRY_DOTENV_VAR)
        if not registry:
            dosa = f'Failed to obtain `{REGISTRY_DOTENV_VAR}`'
            raise InstallerError(dosa)
        docker_srv = Path(registry).parts[0]
        cmd = ['docker', 'login', '--username', config.registry_user, '--password-stdin', docker_srv]
        run_cmd(cmd=cmd, input=TOKEN)

    cmd = PREMAKE_SECRETS_CMD.copy()
    for val in config.explicit_secrets:
        cmd += ['--explicit', val]
    run_cmd(cmd)

    if config.cleanup:
        ep_cmd.append('--drop-data')

    print_out()
    run_cmd(ep_cmd, skip=config.skip_run)

    _deploy_migrations_hook(config=config)


def print_installer_error_and_exit(err: InstallerError) -> NoReturn:
    print_err(40 * '_', '', err, '')
    if err.details:
        print_err(textwrap.indent(str(err.details), INDENT), '')
    if isinstance(err, CheckError):
        print_err(
            'Requiremens check failed',
            'HINT: Checks can be omitted with `--skip-check` (NOT RECOMMENDED)',
            ''
        )
        sys.exit(2)
    print_err('Exit on error', '')
    sys.exit(1)


def list_addons() -> None:
    data = []
    for addon in ADDONS_MODULES:
        data.append(
            {
                'name': addon.name,
                'url': addon.url,
                'base_dir': addon.base_dir,
                'env_file': addon.env_file,
                'is_token_required': addon.is_token_required,
                'license': addon.license,
            }
        )
    print(json.dumps(data, indent=4))


def main() -> None:
    global VERBOSE
    args = get_args()
    VERBOSE = args.verbose

    if args.list_addons:
        list_addons()
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if args.no_cache:
        print_out('', 'Cache cleanup')
        for file in CACHE_DIR.glob(f'*.{GitLabRepo.ARCHIVE_SUFFIX}'):
            print_out(f'Deleting cached {file}')
            file.unlink()

    interactions = Interactions(non_interactive=args.non_interactive)

    if interactions.non_interactive:
        print_out('', 'Non-interactive mode, no confirmations will be asked!', '')

    try:
        Checker(args=args).check()
        conf = ScriptConfigurator(args=args, interactions=interactions).configure()
        download(config=conf)
        configure_system(config=conf)
        with cd(LOCAL_PATH):
            run(config=conf)
    except InstallerError as papa:
        print_installer_error_and_exit(papa)


if __name__ == '__main__':
    main()
