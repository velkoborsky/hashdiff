from dataclasses import dataclass
from typing import Iterable, Any


@dataclass(eq=True, frozen=True)
class HsnapRecord:
    path: str
    size: int
    mtime: float
    digest: Any


def find_duplicate_in_sorted(xs: Iterable):
    """
    For a sorted iterable returns the first duplicate value found or None if there is not any
    """
    try:
        prev, *tail = xs
        for x in tail:
            if x == prev:
                return x
            else:
                prev = x
        return None
    except ValueError:
        return None


