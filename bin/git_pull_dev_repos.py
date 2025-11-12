#! /usr/bin/env python3
"""
git_pull_dev_repos.py is a part of Salt.Box Compose.

Developement helper script to update Git repositories from dev overrides.
"""

# Requires python >= 3.8

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

# Int for limit, None for no limit
PARALLEL_PULLS: int | None = None
LINE = '_' * 40


def get_conf() -> dict:
    bin_dir = Path(__file__).resolve().parent
    bin_path = bin_dir / 'sb-compose.sh'
    cmd = [str(bin_path), 'config', '--format=json']
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        cmd_str = ' '.join(cmd)
        stderr = err.stderr.decode()
        dosa = f'Command failed: {cmd_str}, sterr:\n{stderr}'
        raise RuntimeError(dosa)
    return json.loads(result.stdout)


def get_context_repos(config: dict[str, Any]) -> list[Path]:
    paths = set()
    for service in config.get('services', {}).values():
        if (build := service.get('build')) and (context := build.get('context')):
            paths.add(Path(context))
    cwd = Path.cwd()
    return [p for p in paths if cwd not in p.parents]


def get_volume_repos(config: dict[str, Any]) -> list[Path]:
    sources = set()
    for service in config.get('services', {}).values():
        for vol in service.get('volumes', []):
            sources.add(Path(vol['source']))
    cwd = Path.cwd()
    return [p for p in sources if p.is_absolute() and cwd not in p.parents]


def git_pull(path: Path, lock: threading.Lock) -> int:
    cmd = ['git', '-C', str(path), 'pull']
    res = subprocess.run(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    message = f'{LINE}\n> Git pull {path.name} result:\n{res.stdout.decode()}'
    with lock:
        print(message)
    return res.returncode


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Update Salt.Box source code repositories')
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List detected Git repositories, do not operate'
    )
    parser.add_argument(
        '--no-compose',
        action='store_true',
        help='Skip pulling SaltBox Compose repo itself'
    )
    parser.add_argument(
        '--only-compose',
        action='store_true',
        help='Pull only SaltBox Compose repos, no `.env` required'
    )
    return parser.parse_args()


def action_pull(repos: list[Path]) -> list[Path]:
    pull_failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_PULLS) as executor:
        print_lock = threading.Lock()
        futures = {executor.submit(git_pull, path, print_lock): path for path in repos}
        for fut in concurrent.futures.as_completed(futures.keys()):
            result = fut.result()
            if result:
                pull_failed.append(futures[fut])
    return pull_failed


def action_list(repos: list[Path]) -> None:
    print(LINE)
    for repo in repos:
        print(f'- {repo}')

def main():
    args = get_args()
    conf = get_conf()

    repos = []
    if not args.only_compose:
        context_repos = get_context_repos(conf)
        vol_repos = get_volume_repos(conf)
        repos.extend(set(context_repos) | set(vol_repos))
    if not args.no_compose:
        repos.append(Path.cwd())

    if not len(repos):
        print('No repositories found to pull, exit now', file=sys.stderr)
        return

    print(f'Found {len(repos)} repositories')

    if args.list:
        action_list(repos)
        print(LINE)
        print('List only, exit now')

    else:
        pull_failed = action_pull(repos)
        print(LINE)
        if not pull_failed:
            print('Exit on success')
        else:
            fail_list = '\n'.join([f'  - {p}' for p in pull_failed])
            print(f'Failed to pull following repositories:\n{fail_list}\n', file=sys.stderr)
            print('Exit with warnings', file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err, file=sys.stderr)
        print(f'{LINE}\nExit on error', file=sys.stderr)
        sys.exit(1)
