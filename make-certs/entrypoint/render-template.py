#! /usr/bin/env python3
"""
Simple Jinja-based template renderer.

Usage:
  ./render-template.py FILENAME_1.jinja2 FILENAME_2.jinja2 ... FILENAME_N.jinja2

Custom object `env` is available in templates to obtain environment variables.

Usage:
  env['VAR']
  env.get('VAR')
  env.get('VAR', 'default value')
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import jinja2

TPL_SUFFIXES = {'.tpl', '.jinja', '.jinja2', '.j2'}


class JinjaEnv:
    @staticmethod
    def __getattr__(name: str) -> Any:
        try:
            return os.environ[name]
        except KeyError:
            msg = f'Missing environment variable "{name}"'
            raise KeyError(msg)

    @staticmethod
    def get(name: str, default: Any = None) -> Any:
        return os.environ.get(name, default)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Render template files with enviromnent variables.\n'
            'Template files must have a special suffix like `.tpl`.\n'
            'Rendered files will be saved where templates are by default.'
        ),
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Temlpate files',
    )
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        help='Write rendered files to the directory rather than to the template location',
    )
    return parser.parse_args()


def render(tpl_path: Path, result_path: Path) -> None:
    with tpl_path.open('r') as tpl_f, result_path.open('w') as out_f:
        tpl = jinja2.Template(tpl_f.read())
        data = tpl.render(env=JinjaEnv())
        out_f.write(data)


def main() -> None:
    args = get_args()
    for path in args.files:
        if path.suffix not in TPL_SUFFIXES:
            suf_str = ', '.join(TPL_SUFFIXES)
            msg = f'Unexpected file last suffix "{path.suffix}", should be one of: {suf_str}'
            raise RuntimeError(msg)
        if not args.output_dir:
            out_dir = path.parent
        else:
            out_dir = args.output_dir
        res_path = out_dir / path.stem
        render(tpl_path=path, result_path=res_path)
        print(f'Template {path} rendered to {res_path}')


if __name__ == '__main__':
    main()
