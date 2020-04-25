import logging
import re
import sys
from argparse import Namespace
from pathlib import Path
from typing import Iterable, Dict

import hashdiff.logger
from hashdiff.fileio import InputSource, OutputSink, NullOutputSink, FileOutputSink
from hashdiff.hstool.args import parse_args

log = logging.getLogger(__package__)


def cli_main():
    args_raw = parse_args()  # argparse

    # initialize logger
    hashdiff.logger.initialize_stderr_logger_from_args(args_raw)

    # mapping of cli commands to functions
    func = {
        "filter": cli_filter,
        "ls": cli_ls
    }[args_raw.hst_command]

    func(args_raw)

    sys.exit(0)


def _cli_input_arg_to_input_source(args: Namespace) -> InputSource:
    if (args.input is not None) and (args.input != "-"):
        try:
            input_file = Path(args.input).resolve(strict=True)
            return InputSource(input_file)
        except FileNotFoundError as e:
            log.exception('Unable to resolve source file %s', e.filename)
            raise SystemExit(2)
    else:
        return InputSource()


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

    tree = input_source_to_path_tree(input_source)

    matched_files = {}
    matched_dirs = {}
    not_matched = []

    queries = args.FILE
    if len(queries) == 0:
        queries.append(".")  # list root
    for q in queries:
        try:
            obj, prefix = tree.query(q)
            prefix.append(obj.name)
            full_path = str(Path(*prefix))
            if isinstance(obj, PathFile):
                matched_files[full_path] = obj
            else:
                matched_dirs[full_path] = obj
        except FileNotFoundError:
            not_matched.append(q)

    _cli_ls_print_output(matched_dirs, matched_files, not_matched)

    if len(not_matched) > 0:
        raise SystemExit(2)
    else:
        raise SystemExit(0)


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


def input_source_to_path_tree(input_source: InputSource):
    tree = PathDir(".")

    with input_source as records:
        for h_record in records:
            path = Path(h_record.path)
            parts = path.parts
            tree.add(parts)

    return tree


class PathFile:

    def __init__(self, name):
        self.name = name


class PathDir:

    def __init__(self, name, *contents):
        self.name = name
        self.dirs: Dict[str, PathDir] = {}
        self.files: Dict[str, PathFile] = {}
        for a in contents:
            self.add(a)

    def add(self, parts):

        assert len(parts) > 0

        if len(parts) == 1:
            name = parts[0]
            self.files[name] = PathFile(name)
        else:
            (directory, *rest) = parts
            if directory in self.dirs:
                self.dirs[directory].add(rest)
            else:
                self.dirs[directory] = PathDir(directory, rest)

    def query(self, path):
        if isinstance(path, Path):
            return self.query_parts(path.parts)
        if isinstance(path, str):
            return self.query_parts(Path(path).parts)
        else:
            raise ValueError("Invalid query path", path)

    def query_parts(self, parts, prefix=None):
        if prefix is None:
            prefix = []
        if len(parts) == 0:
            return self, prefix
        elif len(parts) == 1:
            name = parts[0]
            try:
                return self.files[name], prefix
            except KeyError:
                pass
            try:
                return self.dirs[name], prefix
            except KeyError:
                raise FileNotFoundError
        else:
            (directory, *rest) = parts
            try:
                return self.dirs[directory].query_parts(rest, prefix.append(directory))
            except KeyError:
                raise FileNotFoundError
