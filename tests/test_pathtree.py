import pytest
from pathlib import PurePosixPath

from hstool.pathtree import PathDir, PathFile

Dir = PathDir
File = PathFile


@pytest.fixture()
def sample_tree():
    return Dir(".", [
        Dir("foo", [
            Dir("subfoo1"),
            Dir("subfoo2", [
                PathFile("foo_source.py"),
                PathFile("food_source.py")
            ]),
            Dir("foofile.bin"),
            File("main.py")
        ]),
        Dir("bar", [
            Dir("drinks"),
            Dir("food", [
                PathFile("food_source.py")
            ]),
            Dir("bar", [
                Dir("bar", [
                    File("bar")
                ]),
                File("bar")
            ]),
            File("main.py")
        ]),
        File("baz"),
        File("README.txt"),
        File("setup.py"),
        File("main.py")
    ])


def _full_path(tup: tuple):
    obj, path_components = tup
    return "/".join(path_components) + ('/' if isinstance(obj, PathDir) else '')


def test_query_empty(sample_tree):
    matches = sample_tree.query_parts([])
    paths = list(map(_full_path, matches))
    assert paths == ['./']


@pytest.mark.parametrize(('query', 'exp'), [
    ('main.py', ['main.py']),
    ('naim.py', []),
    ('*/main.py', ['foo/main.py', 'bar/main.py']),
    ('**/main.py', ['main.py', 'foo/main.py', 'bar/main.py']),
    ('*', ['foo/', 'bar/', 'baz', 'README.txt', 'setup.py', 'main.py']),
    ('**', ['foo/', 'bar/', 'baz', 'README.txt', 'setup.py', 'main.py']),
    ('bar', ['bar/']),
    ('ba?', ['bar/', 'baz']),
    ('**/nonexistent', []),
    ('**/*.py', ['foo/subfoo2/foo_source.py', 'foo/subfoo2/food_source.py', 'foo/main.py', 'bar/food/food_source.py',
                 'bar/main.py', 'setup.py', 'main.py']),
    ('*/*o*/foo*_source.py', ['foo/subfoo2/foo_source.py', 'foo/subfoo2/food_source.py', 'bar/food/food_source.py']),
    ('**/bar', ['bar/', 'bar/bar/', 'bar/bar/bar/', 'bar/bar/bar', 'bar/bar/bar/bar']),
    ('foo/subfoo[12]', ['foo/subfoo1/', 'foo/subfoo2/'])
])
def test_queries(query, exp, sample_tree):
    matches = sample_tree.query_parts(PurePosixPath(query).parts)
    paths = list(map(_full_path, matches))
    assert set(paths) == set(exp)


def test_query_all(sample_tree):
    matches = sample_tree.query_parts(['**', '*'])
    assert len(matches) == 20
