import logging
import re
import sys
from argparse import Namespace
from pathlib import Path
from typing import Iterable, Set

import hashdiff.logger
from hashdiff.fileio import InputSource, OutputSink, NullOutputSink, FileOutputSink
from hashdiff.hstool.args import parse_args
from hashdiff.hstool.pathtree import input_source_to_path_tree, PathFile, PathDir
from hashdiff.normalize import NormalizePaths

log = logging.getLogger(__package__)


def cli_main():
    args_raw = parse_args()  # argparse

    # initialize logger
    hashdiff.logger.initialize_stderr_logger_from_args(args_raw)

    # mapping of cli commands to functions
    func = {'filter': cli_filter,
            'ls': cli_ls,
            'unique': cli_unique
            }[args_raw.hst_command]

    func(args_raw)

    sys.exit(0)


def _cli_input_arg_to_input_source(args: Namespace) -> InputSource:
    if args.input is None:
        return _cli_path_to_input_source("-")
    else:
        return _cli_path_to_input_source(args.input)


def _cli_path_to_input_source(path: str) -> InputSource:
    if path == "-":
        return InputSource()
    else:
        try:
            input_file = Path(path).resolve(strict=True)
            return InputSource(input_file)
        except FileNotFoundError as e:
            log.exception('Unable to resolve file %s', e.filename)
            raise SystemExit(2)


def cli_filter(args):
    input_source = _cli_input_arg_to_input_source(args)

    matched_sink = NullOutputSink()
    not_matched_sink = NullOutputSink()
    if (args.matched is None) and (args.not_matched is None):  # default: output matched to stdout
        matched_sink = FileOutputSink()
    else:
        if args.matched is not None:
            if args.matched == "-":
                matched_sink = FileOutputSink()
            else:
                matched_sink = FileOutputSink(args.matched)
        if args.not_matched is not None:
            if args.matched == "-":
                not_matched_sink = FileOutputSink()
            else:
                not_matched_sink = FileOutputSink(args.not_matched)

    for p in args.pattern:
        try:
            re.compile(p)
        except re.error as e:
            log.exception("Invalid pattern %s", p)
            raise SystemExit(2)

    filter(
        input_source=input_source,
        patterns=args.pattern,
        matched_sink=matched_sink,
        not_matched_sink=not_matched_sink
    )


def filter(input_source: InputSource,
           patterns: Iterable[str],
           matched_sink: OutputSink, not_matched_sink: OutputSink):
    compiled_patterns = [re.compile(p) for p in patterns]

    with input_source as records:
        with matched_sink as matched:
            with not_matched_sink as not_matched:
                for h_record in records:
                    matches = [p.match(h_record.path) for p in compiled_patterns]
                    if any(matches):
                        matched.write(h_record)
                    else:
                        not_matched.write(h_record)


def cli_ls(args):
    input_source = _cli_input_arg_to_input_source(args)

    if args.normalize_paths:
        input_source.normalize_paths = NormalizePaths.NATIVE

    tree = input_source_to_path_tree(input_source)

    queries = args.FILE

    matched_dirs, matched_files, not_matched = ls(tree, queries)

    _cli_ls_print_output(matched_dirs, matched_files, not_matched)

    if len(not_matched) > 0:
        raise SystemExit(2)
    else:
        raise SystemExit(0)


def ls(tree: PathDir, queries: Iterable[str]):

    matched_files = {}
    matched_dirs = {}
    not_matched = []

    queries = list(queries)
    if len(queries) == 0:
        queries.append(".")  # list root

    for q in queries:
        matches = tree.query(q)
        if not matches:
            not_matched.append(q)
        else:
            for m in matches:
                obj, path_parts = m
                full_path = str(Path(*path_parts))
                if isinstance(obj, PathFile):
                    matched_files[full_path] = obj
                else:
                    matched_dirs[full_path] = obj

    return matched_dirs, matched_files, not_matched


def _cli_ls_print_output(matched_dirs, matched_files, not_matched):
    def print_dir(dir, header=None):
        if header is not None:
            print(f'{header}:')
        files = [f for f in dir.files]
        subdirs = [f'{subdir}/' for subdir in dir.dirs]
        for item in sorted(files + subdirs):
            print(item)

    for n in not_matched:
        log.warning(f"cannot list '%s': No such file or directory", n)
    for f in sorted(matched_files):
        print(f)
    if len(matched_files) == 0 and len(matched_dirs) == 1:
        # print the only dir
        print_dir(next(iter(matched_dirs.values())))
    else:
        is_first = len(matched_files) == 0
        for n, dir in enumerate(sorted(matched_dirs)):
            if not is_first:
                print()
            is_first = False
            print_dir(matched_dirs[dir], dir)


def cli_unique(args):

    input_source = _cli_input_arg_to_input_source(args)

    try:
        output_dst = args.output
    except AttributeError:
        output_dst = None

    exclude_hashes: Set[bytes] = set()

    for exclude_file in args.exclude_from:
        exclude_source = _cli_path_to_input_source(exclude_file)
        with exclude_source as exclude_records:
            for h_record in exclude_records:
                exclude_hashes.add(h_record.digest)

    output_sink = FileOutputSink(output_dst)

    with input_source as records:
        with output_sink as output:
            for h_record in records:
                if h_record.digest not in exclude_hashes:
                    output.write(h_record)
