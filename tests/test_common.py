import pytest

from hashdiff.common import find_duplicate_in_sorted


@pytest.mark.parametrize(
    ('seq', 'exp'),
    [
        ([], None),
        ([2], None),
        ([3, 3], 3),
        ([2, 'D', 'D', 3, 3, 4], 'D'),
    ]
)
def test_find_duplicate_in_sorted(seq, exp):
    assert (find_duplicate_in_sorted(seq) == exp)
