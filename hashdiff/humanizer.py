from math import log2


def humanize_size(size_bytes: int) -> str:
    if (size_bytes < 0):
        raise ValueError()

    if size_bytes == 1:
        return "1 byte"

    suffixes = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    max_order = len(suffixes) - 1
    order = int(log2(size_bytes) / 10) if size_bytes > 0 else 0
    order = min(order, max_order)
    value = int(round(float(size_bytes) / (1 << (order * 10)), 0))
    return f'{value} {suffixes[order]}'


def humanize_size_dual(size_bytes: int) -> str:
    if size_bytes < 1024:
        return humanize_size(size_bytes)
    else:
        return f'{humanize_size(size_bytes)} ({size_bytes} bytes)'


def humanize_time(seconds: float) -> str:
    MINUTE: int = 60
    HOUR: int = 60 * MINUTE
    DAY: int = 24 * HOUR

    # plurals function for adding s if n != 1
    def pl(n: int) -> str:
        return "" if n == 1 else "s"

    if seconds < 1:
        return '<1 second'
    elif seconds < MINUTE:
        s = int(round(seconds, 0))
        return f'{s} second{pl(s)}'
    elif seconds < HOUR:
        m = int(seconds // MINUTE)
        s = int(round(seconds % MINUTE, 0))
        return f'{m} minute{pl(m)} {s} second{pl(s)}'
    elif seconds < DAY:
        h = int(seconds // HOUR)
        m = int(round((seconds % HOUR) / MINUTE, 0))
        return f'{h} hour{pl(h)} {m} minute{pl(m)}'
    else:
        d = int(seconds // DAY)
        h = int(round((seconds % DAY) / HOUR, 0))
        return f'{d} day{pl(d)} {h} hour{pl(h)}'
