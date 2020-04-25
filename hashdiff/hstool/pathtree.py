from collections import namedtuple, deque
from contextlib import suppress
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Deque, Iterable

from hashdiff.fileio import InputSource


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

    def __init__(self, name, contents=None):
        self.name = name
        self.dirs: Dict[str, PathDir] = {}
        self.files: Dict[str, PathFile] = {}
        if contents:
            for c in contents:
                self.add(c)

    def add(self, child):

        if isinstance(child, PathDir):
            self.dirs[child.name] = child
        elif isinstance(child, PathFile):
            self.files[child.name] = child
        elif isinstance(child, list) or isinstance(child, tuple):  # components
            if len(child) == 0:
                raise ValueError
            if len(child) == 1:
                name = child[0]
                self.files[name] = PathFile(name)
            else:
                (directory, *rest) = child
                if directory in self.dirs:
                    self.dirs[directory].add(rest)
                else:
                    self.dirs[directory] = PathDir(directory, [rest])
        else:
            raise ValueError

    def query(self, path):
        if isinstance(path, Path):
            return self.query_parts(path.parts)
        if isinstance(path, str):
            return self.query_parts(Path(path).parts)
        else:
            raise ValueError("Invalid query path", path)

    def query_parts(self, query: Iterable[str], glob_enabled=True):
        """
        Query tree with path parts given as list
        :param query: Query
        :return: List of tuples (object, full_path: str)
        """

        stack_item = namedtuple('stack_item', ['start', 'query', 'prefix'])
        stack: Deque[stack_item] = deque()
        stack.append(stack_item(self, list(query), []))

        hits = []

        def has_glob(s: str) -> bool:
            return bool(set('*?[').intersection(s))

        while stack:
            loc, query, prefix = stack.pop()

            if not query:  # termination for directories
                hits.append((loc, prefix if prefix else ['.']))  # special case for root dir
                continue

            head, *tail = query

            if not tail:  # last component, look for files
                if (not glob_enabled) or (not has_glob(head)):
                    with suppress(KeyError):  # yield the one file, if there
                        hits.append((loc.files[head], prefix + [head]))
                else:
                    for name in loc.files:
                        if fnmatch(name, head):
                            hits.append((loc.files[name], prefix + [name]))

            # look in subpaths
            if (not glob_enabled) or (not has_glob(head)):
                with suppress(KeyError):  # recurse into unique subdirectory, if there
                    stack.append(stack_item(loc.dirs[head], tail, prefix + [head]))
            elif head == '**' and len(tail) > 0:
                # either ** evaluates to nothing and we search in this location
                stack.append(stack_item(loc, tail, prefix))
                # or we try the same search in all subdirectories
                stack.extend(stack_item(loc.dirs[name], query, prefix + [name]) for name in loc.dirs)
            else:
                for name in loc.dirs:
                    if fnmatch(name, head):
                        stack.append(stack_item(loc.dirs[name], tail, prefix + [name]))

        return hits
