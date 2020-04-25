import pytest

from hashdiff.normalize import normalize_path_string_heuristic, NormalizePaths


@pytest.mark.parametrize(('input'), [
    'dir/file',
    'C:\\dir\\subdir\\file.ext'
])
def test_normalize_path_string_none(input):
    assert normalize_path_string_heuristic(NormalizePaths.NONE, input) == input


@pytest.mark.parametrize(('input', 'expected'), [
    ('dir/file', 'dir/file'),
    ('dir\\subdir\\file.bin', 'dir/subdir/file.bin'),
    ('C:\\dir\\subdir\\file.ext', 'C:\\/dir/subdir/file.ext'),
    ('/root/řž', '/root/řž'),
    ('.', '.'),
    ('..', '..'),
])
def test_normalize_path_string_posix(input, expected):
    assert normalize_path_string_heuristic(NormalizePaths.POSIX, input) == expected


@pytest.mark.parametrize(('input', 'expected'), [
    ('dir/file', 'dir\\file'),
    ('dir\\subdir\\file.bin', 'dir\\subdir\\file.bin'),
    ('C:\\dir\\subdir\\file.ext', 'C:\\dir\\subdir\\file.ext'),
    ('/root/řž', '\\root\\řž'),
    ('.', '.'),
    ('..', '..'),
])
def test_normalize_path_string_windows(input, expected):
    assert normalize_path_string_heuristic(NormalizePaths.WINDOWS, input) == expected
