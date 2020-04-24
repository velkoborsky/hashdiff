import logging
import os.path
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from hashdiff.fileio import CompressionType
from hashdiff.hsnap import SCRIPT_NAME

log = logging.getLogger(__package__)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(SCRIPT_NAME)
    parser.add_argument('SRC', nargs='+')

    parser.add_argument('-f', '--file', help='output file name, "-" for stdout', required=True)
    parser.add_argument('-o', '--overwrite', help='overwrite out file if exists', action='store_true')
    parser.add_argument('-v', '--verbose', help='print progress information and statistics', action='count')

    parser.add_argument('-i', '--incremental', help=('quick mode - start from existing hsnap file, '
                                                     'if file size and mtime is unchanged, hash is not recalculated'))

    parser_group_path = parser.add_mutually_exclusive_group()
    parser_group_path.add_argument('--path-absolute', help='output absolute paths', action='store_true')
    parser_group_path.add_argument('--path-relative', help='output paths relative to specified dir', default='')
    parser_group_path.add_argument('--path-common', help='output paths relative to common prefix (default)',
                                   action='store_true')

    parser.add_argument('--pickle', help='output in pickled binary format rather than text (experimental)',
                        action='store_true')

    group_compression = parser.add_mutually_exclusive_group()
    group_compression.add_argument('--xz', help='use xz compression for the output file', action='store_const',
                                   const=CompressionType.XZ)
    group_compression.add_argument('--bzip2', help='use bzip2 compression for the output file', action='store_const',
                                   const=CompressionType.BZIP2)
    group_compression.add_argument('--gzip', help='use gzip compression for the output file', action='store_const',
                                   const=CompressionType.GZIP)

    return parser.parse_args()


def _extract_sources(args) -> List[Path]:
    """
    Resolves all sources to paths
    :param args:
    :return:
    """
    try:
        return [Path(x).resolve(strict=True) for x in args.SRC] if args.SRC else [Path.cwd(), ]
    except FileNotFoundError as e:
        log.exception('Unable to resolve source %s', e.filename)
        raise SystemExit(2)


def _extract_base_path(args, sources: List[Path]) -> Optional[Path]:
    """
    define base for logical file paths, None = absolute paths
    """
    path_args = [args.path_absolute, args.path_relative, args.path_common]

    if args.path_absolute:
        log.debug("Using absolute paths")
        return None

    if args.path_relative:
        path = Path(args.path_relative).resolve()
        log.debug("Using paths relative to %s", path)
    else:  # path_common / default
        common = os.path.commonpath(sources)
        path = Path(common).resolve()
        log.debug("Using paths relative to common path %s", common)
    try:
        path = path.resolve(strict=True)
    except FileNotFoundError as e:
        log.warning('Unable to resolve base path %s', e.filename)
    return path


def _extract_output_file(args) -> Optional[Path]:
    """
    define output file, None = sys.stdout
    """
    if args.file == '-':
        return None

    p = Path(args.file)
    if p.exists() and not args.overwrite:
        raise RuntimeError(f'File {p} already exists and -o/--overwrite argument not specified')
    return p


def _extract_incremental_file(args):
    if not args.incremental:
        return None

    try:
        return Path(args.incremental).resolve(strict=True)
    except FileNotFoundError as e:
        log.exception('Unable to resolve incremental file %s', e.filename)
        raise SystemExit(2)


def _extract_compression(args, output_file):
    compression_args = [args.gzip, args.bzip2, args.xz]
    selected = [x for x in compression_args if x]
    if selected:
        if output_file is None:
            raise SystemExit('Compressed output into stdout not supported')
        return selected[0]
    else:
        return None


def extract_args(args):
    sources = _extract_sources(args)
    base_path = _extract_base_path(args, sources)
    output_file = _extract_output_file(args)
    incremental_file = _extract_incremental_file(args)
    verbose = bool(args.verbose)
    pickle = bool(args.pickle)
    compress = _extract_compression(args, output_file)

    return CliArgs(
        sources=sources,
        base_path=base_path,
        output_file=output_file,
        incremental_file=incremental_file,
        verbose=verbose,
        pickle=pickle,
        compress=compress
    )


@dataclass
class CliArgs:
    sources: List[Path]
    base_path: Optional[Path]
    output_file: Optional[Path]
    incremental_file: Optional[Path]
    verbose: bool
    pickle: bool
    compress: CompressionType
