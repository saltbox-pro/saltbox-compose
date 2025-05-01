#! /bin/env python3

import grp
import json
import os
import pwd
import stat
import subprocess
import sys

from typing import Any

"""
Entrypoint recreates users with JSON file and start SSH server.

Users deleted from users file will be vanished in system. Therefore their home
directories will be untouched.

Users JSON file expected to be in form of array:

    [
        {
            "name": str,
            "uid": int,
            "gid": int,
            "home_dir": str,
            "password": str | "password_file": str,
            "shell": Optional[str]
        }
    ]

"""

UID_MIN = 1000
UID_MAX = 60000
GID_MIN = 1000
GID_MAX = 60000

SSHD_EXEC = '/usr/sbin/sshd'
DEFAULT_SHELL = '/usr/sbin/nologin'


def warn(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


class User:
    def __init__(self, data: dict[str, Any]) -> None:
        self.name = data['name']
        self.uid = data['uid']
        if not UID_MIN <= self.uid <= UID_MAX:
            raise RuntimeError(f'uid={self.uid} but expected to be in [{UID_MIN}, {UID_MAX}]')
        self.gid = data['gid']
        if not GID_MIN <= self.gid <= GID_MAX:
            raise RuntimeError(f'gid={self.gid} but expected to be in [{GID_MIN}, {GID_MAX}]')
        self.home_dir = data['home_dir']
        self.password = self._get_password(data)
        self.shell = data.get('shell') or DEFAULT_SHELL

    @staticmethod
    def _get_password(data: dict[str, Any]) -> Any:
        result = data.get('password')
        if result is None:
            warn(f'No password for {data.get('name')} specified, trying to get a password_file')
            with open(data['password_file'], 'r') as file:
                result = file.read().strip()
        return result

    def create(self) -> None:
        try:
            group = grp.getgrgid(self.gid)
        except KeyError:
            ...
        else:
            warn(f'Deleting existing group name={group.gr_name}, gid={group.gr_gid}')
            subprocess.run(['groupdel', group.gr_name])
        subprocess.run(['groupadd', '--gid', str(self.gid), self.name], check=True)
        subprocess.run([
            'useradd',
            '--shell', self.shell,
            '--groups', 'users',
            '--home-dir', self.home_dir,
            '--uid', str(self.uid),
            '--gid', str(self.gid),
            '--create-home',
            self.name
        ], check=True)
        subprocess.run(
            ['passwd', '--stdin', self.name],
            input=self.password.encode(),
            check=True)

    def fix_home_permissions(self) -> None:
        os.chown(self.home_dir, uid=self.uid, gid=self.gid)
        os.chmod(self.home_dir, stat.S_IRWXU)


def del_users() -> None:
    old_users = [user for user in pwd.getpwall() if UID_MIN <= user.pw_uid <= UID_MAX]
    for user in old_users:
        subprocess.run(['userdel', user.pw_name], check=True)


def create_users(users_file_path) -> None:
    with open(users_file_path, 'r') as file:
        users_data = json.load(file)

    for user_dict in users_data:
        user = User(user_dict)
        user.create()
        user.fix_home_permissions()


def run_sshd(port: Any) -> None:
    # Create host keys if not exists
    subprocess.run(['ssh-keygen', '-A'], check=True)

    # Test run
    subprocess.run(['/usr/sbin/sshd', '-t'], check=True)

    # Replace current script with sshd
    os.execv(SSHD_EXEC, [SSHD_EXEC, '-D', '-e', '-p', str(port)])


if __name__ == '__main__':
    del_users()
    create_users(os.environ['USERS_FILE'])
    run_sshd(os.environ['PORT'])
