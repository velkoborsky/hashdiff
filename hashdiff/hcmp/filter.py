import re
from typing import Iterable

from hashdiff.common import HsnapRecord


def filter_by_path(exclude_patterns: Iterable[str], hsnap_records: Iterable[HsnapRecord]) -> Iterable[HsnapRecord]:
    matchers = [re.compile(pat) for pat in exclude_patterns]
    for h_record in hsnap_records:
        matches = [m.match(h_record.path) for m in matchers]
        if not any(matches):
            yield h_record
