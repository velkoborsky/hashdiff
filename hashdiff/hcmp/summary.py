from typing import Iterable

from hashdiff.common import HsnapRecord
from hashdiff.hcmp.compare import OutputCategoryFormatter


def print_output(output, max_lines: int):

    def file_list_formatter(fs: Iterable[HsnapRecord]):
        h: HsnapRecord
        t: Iterable[HsnapRecord]
        h, *t = fs
        return h.path + (f'\tand {len(t)} more' if t else '')

    output_formatters = [
        OutputCategoryFormatter(name='deleted',
                       title_format=lambda c: f'{c.description}: {len(c.files)}',
                       line_format=lambda f: f.path),
        OutputCategoryFormatter(name='deleted_duplicates',
                       title_format=lambda c: f'{c.description}: {len(c.files)}',
                       line_format=lambda t: f'{t[0].path}\tduplicate of\t{file_list_formatter(t[1])}'),
        OutputCategoryFormatter(name='changed',
                       title_format=lambda c: f'{c.description}: {len(c.files)}',
                       line_format=lambda f: f[0].path),  #same paths
        OutputCategoryFormatter(name='moved',
                       title_format=lambda c: f'{c.description}: {len(c.files)}',
                       line_format=lambda t: f'{t[0].path}\t→\t{t[1].path}'),
        OutputCategoryFormatter(name='added',
                       title_format=lambda c: f'{c.description}: {len(c.files)}',
                       line_format=lambda f: f.path),
        OutputCategoryFormatter(name='added_duplicates',
                       title_format=lambda c: f'{c.description}: {len(c.files)}',
                       line_format=lambda t: f'{t[0].path}\tduplicate of\t{file_list_formatter(t[1])}')
    ]
    output_formatters = dict((ocf.name, ocf) for ocf in output_formatters)

    first_category = True
    for cat in output:
        if first_category:
            first_category = False
        else:
            print()
        formatter = output_formatters[cat.name]
        print(formatter.title_format(cat))
        for f in cat.files[0:max_lines] if max_lines > 0 else cat.files:
            print(formatter.line_format(f))
        if 0 < max_lines < len(cat.files):
            print(f'[...{len(cat.files) - max_lines} more...]')