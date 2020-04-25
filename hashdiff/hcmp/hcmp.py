import pickle
import sys
from pathlib import Path
from typing import Iterable

import hashdiff.hcmp.filter as filter
import hashdiff.logger
from hashdiff.fileio import read_input_file
from hashdiff.hcmp.args import parse_args, extract_args
from hashdiff.hcmp.compare import changes
from hashdiff.hcmp.summary import print_output
from hashdiff.normalize import NormalizePaths


def cli_main():
    args_raw = parse_args()  # argparse
    cli_args = extract_args(args_raw)  # processing argparse output

    # initialize logger
    hashdiff.logger.initialize_stderr_logger_from_args(args_raw)

    output = main(cli_args.prev, cli_args.curr, cli_args.normalize_paths)

    print_output(output, cli_args.max_lines)

    if cli_args.store_result:
        with cli_args.store_result.open('wb') as f:
            pickle.dump(output, f)

    sys.exit(0)


def main(prev: Path, curr: Path, normalize_paths: NormalizePaths, exclude_paths: Iterable[str] = []):
    prev_records = read_input_file(prev, normalize_paths=normalize_paths)
    curr_records = read_input_file(curr, normalize_paths=normalize_paths)

    exclude_paths = list(exclude_paths)
    prev_records = list(filter.filter_by_path(exclude_paths, prev_records))
    curr_records = list(filter.filter_by_path(exclude_paths, curr_records))

    output = changes(prev_records, curr_records)

    return output
