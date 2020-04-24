import dataclasses
import logging
import os.path
import sys
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional

from hashdiff.common import HsnapRecord
from hashdiff.fileio import OutputSink, read_input_file, FileOutputSink
from hashdiff.hsnap.args import parse_args, extract_args
from hashdiff.hsnap.hash import file_sha512
from hashdiff.hsnap.walk import scan_paths_for_files, FileStat
from hashdiff.humanizer import humanize_time, humanize_size, humanize_size_dual
import hashdiff.logger

log = logging.getLogger(__package__)


class ProcessingStats:

    def __init__(self, total_size, total_files, incremental_enabled, start_time):

        self.total_size = total_size
        self.total_files = total_files
        self.size_processed = 0
        self.files_processed = 0
        self.last_displayed_size = 0
        self.last_displayed_time = perf_counter()

        self.incremental_enabled = incremental_enabled
        self._incremental_reused = 0
        self._incremental_different = 0
        self._incremental_new = 0

        self.start_time = start_time

    LOGGING_INTERVAL = 1  # second

    def increment(self, size, files=1):
        self.size_processed = self.size_processed + size
        self.files_processed = self.files_processed + files

    def incremental_reused(self):
        self._incremental_reused = self._incremental_reused + 1

    def incremental_different(self):
        self._incremental_different = self._incremental_different + 1

    def incremental_new(self):
        self._incremental_new = self._incremental_new + 1

    def log_processing_start(self):
        if log.getEffectiveLevel() > logging.INFO:
            return
        log.info('Processing files')
        log.info(f'Total size: {humanize_size_dual(self.total_size)}')
        log.info(f'Number of files: {self.total_files}')

    def log_progress(self):
        if log.getEffectiveLevel() > logging.INFO:
            return

        current_time = perf_counter()
        time_since_last = current_time - self.last_displayed_time
        if time_since_last < self.LOGGING_INTERVAL:
            return

        processed_percentage = round(100 * self.size_processed / self.total_size, 1) if self.total_size > 0 else 100.
        try:
            processed_since_last = self.size_processed - self.last_displayed_size
            current_speed = processed_since_last / time_since_last  # bytes/second
            eta = (self.total_size - self.size_processed) / current_speed  # seconds
            log.info(f'{processed_percentage}% done, '
                     f'current speed: {humanize_size(int(round(current_speed, 0)))}/s, '
                     f'estimated time left: {humanize_time(eta)}')
        except (OverflowError, ZeroDivisionError):
            log.info(f"{processed_percentage}% done")

        self.last_displayed_time = current_time
        self.last_displayed_size = self.size_processed

    def log_summary(self):
        if log.getEffectiveLevel() > logging.INFO:
            return

        log.info(f'Processing complete')
        log.info(f'Processed size: {humanize_size_dual(self.size_processed)}')
        log.info(f"Processed files: {self.files_processed}")
        if self.incremental_enabled:
            log.info(f"Incremental: {self._incremental_reused} reused, "
                     f"{self._incremental_different} different, "
                     f"{self._incremental_new} new")

        end_time = perf_counter()
        time_elapsed = end_time - self.start_time
        log.info(f"Time elapsed: {humanize_time(time_elapsed)}")
        average_speed = self.size_processed / time_elapsed if time_elapsed > 0 else float('inf')
        log.info(f"Average speed: {humanize_size(average_speed)}/s")


def cli_main():
    args_raw = parse_args()  # argparse
    cli_args = extract_args(args_raw)  # processing argparse output

    # initialize logger
    hashdiff.logger.initialize_stderr_logger_from_args(args_raw)

    main(**dataclasses.asdict(cli_args))  # run main

    sys.exit(0)


def _read_incremental_catalog(incremental_file: Optional[Path]) -> Optional[Dict]:
    if not incremental_file:
        return None
    log.info("Reading incremental catalog")
    incremental_records = read_input_file(incremental_file)
    incremental_dict = dict((h_rec.path, h_rec) for h_rec in incremental_records)
    return incremental_dict


def main(sources, base_path, output_file, incremental_file, pickle, compress, **kwargs):
    start_time = perf_counter()

    # scan for files
    files: List[FileStat] = list(scan_paths_for_files(sources))

    # calculate total size for progress tracking progress tracking
    total_size = sum(f.size for f in files)
    num_files = len(files)

    # read incremental catalog
    incremental_dict = _read_incremental_catalog(incremental_file)

    # create processing statistics tracker and logger
    stats = ProcessingStats(total_size, num_files, (incremental_dict is not None), start_time)
    stats.log_processing_start()

    # open output file
    with FileOutputSink(output_file, binary_pickle=pickle, compression=compress) as output_sink:
        run(files, base_path, output_sink, incremental_dict, stats)

    stats.log_summary()


def run(files: List[FileStat], base_path: Optional[Path], output_sink: OutputSink, incremental_dict: Dict,
        stats: ProcessingStats):
    def relpath(file_path: Path):
        nonlocal base_path
        if base_path is None:
            return str(file_path)
        else:
            # noinspection PyTypeChecker
            return str(os.path.relpath(file_path, base_path))

    def cached_digest(log_path: str, file: FileStat):
        nonlocal incremental_dict
        if incremental_dict:
            try:
                cached = incremental_dict[log_path]
                if cached.size == file.size and cached.mtime == file.mtime:
                    stats.incremental_reused()
                    return cached.digest
                else:
                    stats.incremental_different()
            except KeyError:
                stats.incremental_new()
        return None

    for f in files:
        logical_path = relpath(f.path)

        # try to use incremental, calculate if not available
        digest = cached_digest(logical_path, f) or file_sha512(f.path)

        h_record = HsnapRecord(logical_path, f.size, f.mtime, digest)
        output_sink.write(h_record)

        stats.increment(f.size)
        stats.log_progress()
