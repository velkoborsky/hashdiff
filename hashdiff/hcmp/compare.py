from collections import namedtuple
from itertools import groupby
from typing import Iterable

from hashdiff.common import HsnapRecord, find_duplicate_in_sorted

OutputCategory = namedtuple('OutputCategory', 'name, description, files')
OutputCategoryFormatter = namedtuple('OutputCategoryFormatter', 'name, title_format, line_format')


def changes(previous: Iterable[HsnapRecord], current: Iterable[HsnapRecord]):
    """
    Path based comparison of changes - primarily for reporting changes of the same data set in time
    :param previous:
    :param current:
    :param max_lines:
    :return:
    """

    def sort_by_path(xs):
        return sorted(xs, key=lambda f: f.path, reverse=True)

    prev = sort_by_path(previous)
    curr = sort_by_path(current)

    for xs in [prev, curr]:
        paths = [x.path for x in xs]
        dup = find_duplicate_in_sorted(paths)
        if dup is not None:
            raise RuntimeError(f'Duplicate path found {dup}, use simple diff instead of changes.')

    # 1st pass - find differences by path
    missing = list()
    added = list()
    unchanged = list()
    while len(prev) and len(curr):
        if prev[-1].path == curr[-1].path:  # from end, on reverse sorted
            p: HsnapRecord = prev.pop()
            c: HsnapRecord = curr.pop()
            if p.digest == c.digest:
                unchanged.append(p)
                pass
            else:
                # either changed or moved and replaced
                missing.append(p)
                added.append(c)
        elif prev[-1].path < curr[-1].path:
            missing.append(prev.pop())
        elif prev[-1].path > curr[-1].path:
            added.append(curr.pop())
        else:
            raise RuntimeError(f'Unable to compare {prev[-1]} and {curr[-1]}')
    # one of the lists empty - add rest
    while prev:
        missing.append(prev.pop())
    while curr:
        added.append(curr.pop())
    del prev, curr

    # 2nd pass - in missing/added list try to find moved files
    moved = []
    missing_buf = []
    added_buf = []
    for xs in [missing, added]:
        xs.sort(key=lambda f: f.digest, reverse=True)
    while len(missing) and len(added):
        m = missing[-1]
        a = added[-1]
        if m.digest == a.digest:
            moved.append((missing.pop(), added.pop()))
        elif m.digest < a.digest:
            missing_buf.append(missing.pop())
        elif m.digest > a.digest:
            added_buf.append(added.pop())
        else:
            raise RuntimeError(f'Unable to compare {m} and {a}')
    # merge back
    missing.extend(missing_buf)
    added.extend(added_buf)
    del missing_buf, added_buf

    # 3rd pass - changed files
    changed = []
    missing_buf = []
    added_buf = []
    for xs in [missing, added]:
        xs.sort(key=lambda f: f.path, reverse=True)
    while len(missing) and len(added):
        m = missing[-1]
        a = added[-1]
        if m.path == a.path:
            changed.append((missing.pop(), added.pop()))
        elif m.path < a.path:
            missing_buf.append(missing.pop())
        elif m.path > a.path:
            added_buf.append(added.pop())
        else:
            raise RuntimeError(f'Unable to compare {m} and {a}')
    # merge back
    missing.extend(missing_buf)
    added.extend(added_buf)
    del missing_buf, added_buf

    # 4th pass for added find out if it is a copy, for delete if it had been the last copy
    # for both find out if it is empty
    added_new = []
    added_copy = []
    deleted_last = []
    deleted_copy = []

    def group_by_digest(xs: Iterable[HsnapRecord]) -> dict:
        def key_func(f: HsnapRecord): return f.digest

        return dict([(k, list(v)) for k, v in groupby(sorted(xs, key=key_func), key=key_func)])

    current_by_digest = group_by_digest(current)
    previous_by_digest = group_by_digest(previous)
    for a in added:
        try:
            added_copy.append((a, previous_by_digest[a.digest]))
        except KeyError:
            added_new.append(a)
    del added
    for d in missing:
        try:
            deleted_copy.append((d, current_by_digest[d.digest]))
        except KeyError:
            deleted_last.append(d)
    del missing

    output = [
        OutputCategory(name='deleted', files=deleted_last, description='Deleted (no copy left)'),
        OutputCategory(name='deleted_duplicates', files=deleted_copy,
                       description='Deleted duplicates (some copies left)'),
        OutputCategory(name='changed', files=changed, description='Changed (same path, different file)'),
        OutputCategory(name='moved', files=moved, description='Moved (same file, different path)'),
        OutputCategory(name='added', files=added_new, description='Added (new files)'),
        OutputCategory(name='added_duplicates', files=added_copy,
                       description='Added duplicates (of previously existing)')
    ]

    return output
