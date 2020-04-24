import logging

from argparse import Namespace


def initialize_stderr_logger_from_args(args: Namespace):
    try:
        verbosity = args.verbose
        if verbosity is None:
            level = logging.WARNING
        elif verbosity >= 2:
            level = logging.DEBUG
        elif verbosity >= 1:
            level = logging.INFO
        else:
            level = logging.WARNING
    except AttributeError:
        level = logging.WARNING

    initialize_stderr_logger(level)


def initialize_stderr_logger(level: int):
    log = logging.getLogger(__package__)
    stderr = logging.StreamHandler()

    log.setLevel(level)
    stderr.setLevel(level)

    log.addHandler(stderr)
