import logging
import argparse
from argparse import ArgumentParser

from hashdiff.hstool import SCRIPT_NAME

log = logging.getLogger(__package__)


def construct_parser(parser: ArgumentParser):
    commands = parser.add_subparsers(help='available commands, use commands -h for usage',
                                     dest='hst_command', required=True,
                                     description='The tool is a collection of commands, as listed below')

    filter = commands.add_parser('filter',
                                 help='filters/splits input file based on regex pattern match',
                                 description='The filter command allows to filter (include/exclude) or split existing '
                                             'hsnap files based on path regex patterns. Unless specified otherwise, '
                                             'expects stdin input and writes matched records to stdout.')
    parser_extend_workaround(filter)  # needed for python < 3.8

    filter_g = filter.add_argument_group("filter command")
    filter_g.add_argument('--input', '-i', help='input file, "-" for stdin')
    filter_g.add_argument('--pattern', '-p', help='path regexp in Python re module format, can be specified multiple '
                                                  'times with multiple patterns functioning as OR',
                          action='append', required=True)
    filter_g.add_argument('--matched', '-m', help='output file for records matching any of the patterns')
    filter_g.add_argument('--not-matched', '-n', help='output file for records not matching any of the patterns')

    ls = commands.add_parser('ls',
                             help='lists hsn file contents as if it was a directory')
    parser_extend_workaround(ls)  # needed for python < 3.8

    ls_g = ls.add_argument_group("ls command")
    ls_g.add_argument('--input', '-i', help='input file, "-" for stdin')
    ls_g.add_argument('FILE', nargs='*', action='extend', help='files to be listed, supporting glob syntax')
    ls_g.add_argument('--normalize-paths', help='Normalize path to native style before listing', action='store_true')


def parse_args():
    parser = ArgumentParser(SCRIPT_NAME)
    construct_parser(parser)
    return parser.parse_args()


def parser_extend_workaround(parser: ArgumentParser):
    if not parser._registry_get('action', 'extend'):
        class ExtendAction(argparse._AppendAction):
            def __call__(self, parser, namespace, values, option_string=None):
                items = getattr(namespace, self.dest) or []
                items.extend(values)
                setattr(namespace, self.dest, items)

        parser.register('action', 'extend', ExtendAction)
