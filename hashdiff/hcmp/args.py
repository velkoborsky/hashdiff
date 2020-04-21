import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from argparse import ArgumentParser

from hashdiff.hcmp import SCRIPT_NAME
from hashdiff.hcmp.normalize import NormalizePaths

log = logging.getLogger(__package__)


def construct_parser(parser: ArgumentParser):
    parser.add_argument('PREV', help='hsnap file with previous/original state ')
    parser.add_argument('CURR', help='hsnap file with current/new state')

    parser.add_argument('--normalize-paths',
                        help='Normalize path to POSIX/Windows style before comparing, default: posix',
                        choices=[x.name.lower() for x in NormalizePaths],
                        type=str.lower,
                        default=NormalizePaths.POSIX.name.lower()
                        )

    parser.add_argument('-n', '--lines', help='number of lines to print into console, 0 -> unlimited',
                        type=int, default=10)
    parser.add_argument('--store-result', help='pickles result into a binary file for further analysis in python')
    parser.add_argument('-o', '--overwrite', help='overwrite out files if they exists', action='store_true')


def parse_args():
    parser = ArgumentParser(SCRIPT_NAME)
    construct_parser(parser)
    return parser.parse_args()


def extract_args(args):
    try:
        prev = Path(args.PREV).resolve(strict=True)
        curr = Path(args.CURR).resolve(strict=True)
    except FileNotFoundError as e:
        log.exception('Unable to resolve source file %s', e.filename)
        raise SystemExit(2)

    normalize_paths = NormalizePaths[args.normalize_paths.upper()]  # values enforced by choices

    max_lines: int = int(args.lines)

    if not args.store_result:
        store_result = None
    else:
        store_result = Path(args.store_result).resolve()
        if store_result.exists() and not args.overwrite:
            log.error(f'File {store_result} already exists and -o/--overwrite argument not specified')
            raise SystemExit(2)

    return CliArgs(
        prev=prev,
        curr=curr,
        normalize_paths=normalize_paths,
        max_lines=max_lines,
        store_result=store_result
    )


@dataclass
class CliArgs:
    prev: Path
    curr: Path
    normalize_paths: NormalizePaths
    max_lines: int
    store_result: Optional[Path]
