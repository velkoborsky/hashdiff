import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Set, List, Iterable

log = logging.getLogger(__package__)


@dataclass
class FileStat:
    path: Path
    size: int
    mtime: float


def scan_paths_for_files(paths: List[Path]) -> Iterable[FileStat]:
    visited_inodes = set()  # shared set of already visited files

    log.info(f'Scanning for files')
    for p in paths:
        log.info(f'Scanning path: {p}')
        for fs in _scan_path(p, visited_inodes):
            yield fs
    log.info(f'Scanning complete')


def _file_path_to_stat(file_path: Path) -> FileStat:
    stat = file_path.stat()
    size = stat.st_size
    mtime = stat.st_mtime
    return FileStat(file_path, size, mtime)


def _scan_path(root_path: Path, visited_inodes: Set = None) -> Iterable[FileStat]:
    """
    Recursively scans root for files
    :param root_path: root of walk from which we do not exit, usually dir but file also works
    :param visited_inodes: set of already visited inodes (will be skipped, new visited will be added)
    :return: Path objects of files found
    """

    if not visited_inodes:
        visited_inodes = set()

    root = root_path.resolve(strict=True)

    def visit(p: Path):

        # resolve absolute path, check file exists
        try:
            r = p.resolve(strict=True)
        except FileNotFoundError as e:
            if p.is_symlink():
                log.warning('Invalid link {} pointing to non-existing {}'.format(p, r))
            else:
                raise e  # unexpected

        # check whether we are still in root
        if root not in r.parents and not root == r:
            log.warning('Skipping link {} pointing to {} outside of {}'.format(p, r, root))
            return

        # check whether we have not yet visited this file/inode
        inode = p.stat().st_ino  # if p had been a symlink, this returns target stat; lstat for link
        if inode in visited_inodes:
            return
        visited_inodes.add(inode)

        # yield file or recurse
        try:
            if r.is_file():
                yield _file_path_to_stat(r)
            # for a directory, visit children
            elif r.is_dir():
                children = r.iterdir()
                for c in children:
                    yield from visit(c)
            # skip special types
            elif r.is_block_device():
                log.warning('Skipping block device: {}'.format(r))
            elif r.is_char_device():
                log.warning('Skipping char device: {}'.format(r))
            elif r.is_fifo():
                log.warning('Skipping FIFO: {}'.format(r))
            elif r.is_socket():
                log.warning('Skipping socket: {}'.format(r))
            else:
                log.error("Unknown file type: {}".format(r))
        except FileNotFoundError as e:
            log.warning('File not found: {} -- {}: {}'.format(p, e.strerror, e.filename))
        except PermissionError as e:
            log.warning('Permission Error: {} -- {}: {}'.format(p, e.strerror, e.filename))

    yield from visit(root_path)
