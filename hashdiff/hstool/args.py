import logging
import argparse
from argparse import ArgumentParser

from hashdiff.hstool import SCRIPT_NAME

log = logging.getLogger(__package__)


def construct_parser(parser: ArgumentParser):
    commands = parser.add_subparsers(help='available commands, use commands -h for usage',
                                     dest='hst_command', required=True,
                                     description='The tool is a collection of commands, as listed below')

    construct_parser_filter(commands)
    construct_subparser_ls(commands)
    construct_subparser_unique(commands)


def construct_parser_filter(commands):
    cmd = commands.add_parser('filter', help='filters/splits input file based on regex pattern match',
                              description='The filter command allows to filter (include/exclude) or split existing '
                                          'hsnap files based on path regex patterns. Unless specified otherwise, '
                                          'expects stdin input and writes matched records to stdout.')
    parser_extend_workaround(cmd)  # needed for python < 3.8

    group = cmd.add_argument_group("filter command")
    group.add_argument('--input', '-i', help='input file, "-" for stdin')
    group.add_argument('--pattern', '-p', help='path regexp in Python re module format, can be specified multiple '
                                               'times with multiple patterns functioning as OR',
                       action='append', required=True)
    group.add_argument('--matched', '-m', help='output file for records matching any of the patterns')
    group.add_argument('--not-matched', '-n', help='output file for records not matching any of the patterns')


def construct_subparser_ls(commands):
    cmd = commands.add_parser('ls', help='lists hsn file contents as if it was a directory')
    parser_extend_workaround(cmd)  # needed for python < 3.8

    grp = cmd.add_argument_group("ls command")
    grp.add_argument('--input', '-i', help='input file, "-" for stdin')
    grp.add_argument('FILE', nargs='*', action='extend', help='files to be listed, supporting glob syntax')

    grp = cmd.add_argument_group("input/output options")
    grp.add_argument('--normalize-paths', help='Normalize path to native style before listing', action='store_true')


def construct_subparser_unique(commands):
    cmd = commands.add_parser('unique', help='selects files, whose hash is only in input, not in exclude-from files')
    parser_extend_workaround(cmd)  # needed for python < 3.8

    grp = cmd.add_argument_group("unique command")
    grp.add_argument('--input', '-i', help='input file, "-" for stdin')
    grp.add_argument('--exclude-from', '-e', nargs='*', action='extend',
                     help='input file, "-" for stdin', required=True)
    grp.add_argument('--output', '-o', help='output file, "-" for stdout')


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
