import pytest
from hashdiff.humanizer import humanize_size, humanize_size_dual, humanize_time


def test_humanize_size():
    cases = [
        (0, '0 bytes'),
        (1, '1 byte'),
        (2, '2 bytes'),
        (1023, '1023 bytes'),
        (1024, '1 KiB'),
        (1500, '1 KiB'),
        (1535, '1 KiB'),
        (1536, '2 KiB'),
        (3 * 1024 * 1024, '3 MiB'),
        (9 * 1024 ** 3, '9 GiB'),
        (100 * 1024 ** 4, '100 TiB'),
        (1000 * 1024 ** 5, '1000 PiB'),
        (1023 * 1024 ** 6, '1023 EiB'),
        (1024 ** 7, '1 ZiB'),
        (42 * 1024 ** 8, '42 YiB'),
        (123456786 * 1024 ** 8, '123456786 YiB')
    ]
    for arg, res in cases:
        assert (humanize_size(arg) == res)

    with pytest.raises(ValueError):
        humanize_size(-2)


def test_humanize_size_dual():
    assert (humanize_size_dual(0) == '0 bytes')
    assert (humanize_size_dual(1) == '1 byte')
    assert (humanize_size_dual(2) == '2 bytes')
    assert (humanize_size_dual(1023) == '1023 bytes')
    assert (humanize_size_dual(1234) == '1 KiB (1234 bytes)')


def test_humanize_time():
    cases = [
        (0.1, '<1 second'),
        (0.99, '<1 second'),
        (1., '1 second'),
        (1.49, '1 second'),
        (1.5, '2 seconds'),
        (65.5, '1 minute 6 seconds'),
        (120.3, '2 minutes 0 seconds'),
        (38123.45, '10 hours 35 minutes'),
        (123456789., '1428 days 22 hours')

    ]
    for x, exp in cases:
        y = humanize_time(x)
        assert (y == exp)
