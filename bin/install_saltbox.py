#! /usr/bin/env python3

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HTTP_CHUNK_BYTE = 8192
HTTP_TIMEOUT_SEC = 30
GITLAB_SERVER = 'dev.saltbox.pro'
COMPOSE_PROJ = 'saltbox/saltbox-compose'
SUFFIX = 'tar.gz'

URL_TPL = 'https://{host}/{group}/{project}/-/archive/master/{project}-{ref}.{suffix}'
url = 'https://dev.saltbox.pro/saltbox/saltbox-compose/-/archive/413e8f42b75476edae2663098369e58805a0572b/saltbox-compose-413e8f42b75476edae2663098369e58805a0572b.tar.gz'
url = 'https://dev.saltbox.pro/saltbox/saltbox-compose/-/archive/v0.1.2/saltbox-compose-v0.1.2.tar.gz?ref_type=tags'


class GitLabRepo:
    def __init__(self, url: str) -> None:
        url = urllib.parse.urlparse(url)
        path = Path(url.path)
        self.scheme = url.scheme
        self.server = url.netloc
        self.owner = str(path.parent).lstrip('/')
        self.project = path.name


    def get_tags(self) -> None:
        url = (
            f'{self.scheme}://{self.server}/api/v4/projects/'
            f'{self.owner}%2F{self.project}/repository/tags'
        )
        resp = urllib.request.urlopen(url)
        body = json.load(resp)
        return [i['name'] for i in body]


COMPOSE_REPO = GitLabRepo('https://dev.saltbox.pro/saltbox/saltbox-compose')


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


def download() -> None:
    print(COMPOSE_REPO.get_tags())


def configure() -> None:
    ...


def run() -> None:
    ...


def main() -> None:
    download()
    configure()
    run()


if __name__ == '__main__':
    main()
