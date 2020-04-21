from enum import Enum
from pathlib import PurePosixPath, PureWindowsPath, PurePath

from hashdiff.common import HsnapRecord


class NormalizePaths(Enum):
    POSIX = 0
    WINDOWS = 1
    NONE = 2


_non_printable_chars = set(chr(n) for n in range(1, 32))
_windows_path_forbidden_chars = {'*', '"', '/', '?', '<', '|', '>'}.union(_non_printable_chars)


def _path_from_string_heuristic(path: str) -> PurePath:
    if _windows_path_forbidden_chars.intersection(path):
        return PurePosixPath(path)  # POSIX for sure, Windows does not allow
    elif '\\' in path:
        return PureWindowsPath(path) # Guessing Windows, could be part of a POSIX filename
    else:
        return PurePosixPath(path) # Else take POSIX as default, should not make a difference


def normalize_path_string_heuristic(style: NormalizePaths, path: str) -> str:
    if style == NormalizePaths.NONE:
        return path
    else:
        p = _path_from_string_heuristic(path)
        if style == NormalizePaths.POSIX:
            return str(PurePosixPath(p))
        elif style == NormalizePaths.WINDOWS:
            return str(PureWindowsPath(p))
    raise NotImplemented()


def normalize_hsnap_record(path_style: NormalizePaths, hsnap_record: HsnapRecord) -> HsnapRecord:
    normalized_path = normalize_path_string_heuristic(path_style, hsnap_record.path)
    return HsnapRecord(
        path=normalized_path,
        size=hsnap_record.size,
        mtime=hsnap_record.mtime,
        digest=hsnap_record.digest
    )
