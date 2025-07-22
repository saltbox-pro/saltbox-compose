#! /usr/bin/env python3
"""
git_pull_dev_repos.py is a part of Salt.Box Compose.

Developement helper script to update Git repositories from dev overrides.
"""

import concurrent.futures
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

LINE = '_' * 40
# Int for limit, None for no limit
PARALLEL_PULLS: int | None = None

def get_conf() -> dict:
    cmd = ['docker', 'compose', 'config']
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        cmd_str = ' '.join(cmd)
        stderr = err.stderr.decode()
        dosa = f'Command failed: {cmd_str}, sterr:\n{stderr}'
        raise RuntimeError(dosa)
    return yaml.safe_load(result.stdout)


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


def main():
    conf = get_conf()
    context_repos = get_context_repos(conf)
    vol_repos = get_volume_repos(conf)
    repos = list(set(context_repos) | set(vol_repos))
    repos.append(Path.cwd())
    pull_failed = []

    print(f'Found {len(repos)} repositories')

    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_PULLS) as executor:
        print_lock = threading.Lock()
        futures = {executor.submit(git_pull, path, print_lock): path for path in repos}
        for fut in concurrent.futures.as_completed(futures.keys()):
            result = fut.result()
            if result:
                pull_failed.append(futures[fut])
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
