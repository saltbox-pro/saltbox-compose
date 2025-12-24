#! /usr/bin/env python3

# Validate Salt.Box specific dotenv file.
# Usage:
#   ./bin/validate_dotenv.py
#
# Script may produce non-zero exit code on technically valid Compose dotenv file
# because of style warnings.
#
# Script currently does not support in-qoutes linebreakes, only single line
# declarations.
#

import dataclasses
import re
import sys
from pathlib import Path
from typing import Dict, List

REF_FILE = Path('example.env')
ENV_FILE = Path('.env')
EXTRA_ENV_VAR = '_UPDATE_AND_RUN_EXTRA_ENV_FILES'

_kc_adm_msg='KEYCLOAK_ADMIN_* variables replaced by SALTBOX_ADMIN_*'
_mock_minion_msg='SALT_MOC_MINION* variables replaced by SALT_MOCK_MINION*'
DEPRECATIONS = {
    'BACKEND_HOST': 'Obsolete on v0.0.2',

    'WEB_SERVER_SCHEME': 'HTTPS is the only proto after v0.0.2',
    'WEB_SERVER_WS_SCHEME': 'WSS is the only proto after v0.0.2',
    'KEYCLOAK_ADMIN_NAME': _kc_adm_msg,

    'KEYCLOAK_ADMIN_LASTNAME': _kc_adm_msg,
    'KEYCLOAK_ADMIN_FIRSTNAME': _kc_adm_msg,
    'KEYCLOAK_ADMIN_EMAIL': _kc_adm_msg,

    'SALT_MOC_MINION_LOG_LEVEL': _mock_minion_msg,
    'SALT_MOC_MINION_RETRY_DNS': _mock_minion_msg,
    'SALT_MOC_MINION_REPLICAS': _mock_minion_msg,

    'BACKEND_HTTP_PORT': 'Replaced by CORE_PORT',
    'MONGO_PORT': 'Use MONGO_EXPOSE_SOCKET instead',
}


VAR_RE = re.compile(r'^\s*(?P<name>\w*)\s*[=:]\s*(?P<val>\S.*)')
QUOTED_VAR_RE = re.compile(r'^\s*(?P<name>\w*)\s*[=:]\s*(?P<quote>[\'"])(?P<val>.*)(?P=quote)')
COMMENT_RE = re.compile(r'^\s*#.*')
EMPTY_LINE_RE = re.compile(r'^\s*$')
TRAILING_SPACES_RE = re.compile(r'^.*\s+$')

WARN_COUNTER = 0


class ValidationError(ValueError): ...


@dataclasses.dataclass
class Entry:
    name: str
    val: str
    file: Path
    line: int


def warn(msg: str, prefix='WARN') -> None:
    global WARN_COUNTER
    WARN_COUNTER += 1
    print('>', prefix, msg, file=sys.stderr)


def parse_val_extra(val: str) -> List[Path]:
    return [Path(token) for token in val.split(',')]


def parse(dotenv: Path) -> Dict[str, Entry]:
    result = {}
    try:
        iter = dotenv.read_text().splitlines()
    except OSError as err:
        raise ValidationError(err) from None
    for num, line in enumerate(iter, start=1):
        if TRAILING_SPACES_RE.match(line):
            warn(f'Trailing spaces in `{dotenv}`, line {num}')
        match = QUOTED_VAR_RE.match(line)
        if match:
            result[match.group('name')] = Entry(
                name=match.group('name'),
                val=match.group('val'),
                file=dotenv,
                line=num,
            )
            continue
        match = VAR_RE.match(line)
        if match:
            result[match.group('name')] = Entry(
                name=match.group('name'),
                val=match.group('val').strip(),
                file=dotenv,
                line=num,
            )
            continue
        if COMMENT_RE.match(line) or EMPTY_LINE_RE.match(line):
            continue
        dosa = f'Misformed line {line} in `{dotenv}`'
        raise ValidationError(dosa)
    return result


def main() -> None:
    ref = parse(REF_FILE)
    current = parse(ENV_FILE)
    extra_dotenvs = []

    extra_env_val = current.get(EXTRA_ENV_VAR)

    if extra_env_val:
        extra_dotenvs = parse_val_extra(extra_env_val.val)

    for extra_path in extra_dotenvs:
        ref.update(parse(extra_path))

    for name, entry in current.items():
        deprecation = DEPRECATIONS.get(name)
        if deprecation:
            warn(f'File `{entry.file}` line {entry.line}: {deprecation}')
            continue
        if name not in ref:
            dosa = f'Unexpected variable `{name}` in `{entry.file}` line {entry.line}'
            raise ValidationError(dosa)

if __name__ == '__main__':
    try:
        main()
    except ValidationError as err:
        warn(str(err), prefix='ERROR')
        sys.exit(1)

    if WARN_COUNTER:
        warn(f'Total warnings: {WARN_COUNTER}')
        sys.exit(1)
