import bz2
import gzip
import logging
import lzma
import pickle
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, List

from hashdiff.common import HsnapRecord
from hashdiff.serialize import serialize, deserialize

log = logging.getLogger(__name__)


class CompressionType(Enum):
    XZ = 1
    BZIP2 = 2
    GZIP = 3
    none = None


def opener_based_on_compression_flag(compress):
    if compress is None:
        opener = open
    else:
        opener = {
            CompressionType.XZ: lzma.open,
            CompressionType.BZIP2: bz2.open,
            CompressionType.GZIP: gzip.open,
            CompressionType.none: open
        }[compress]
    return opener


def input_file_type_heuristic(path: Path):
    if path.suffix == '.xz':
        compression = CompressionType.XZ
    elif path.suffix == '.bz2':
        compression = CompressionType.BZIP2
    elif path.suffix in ['.gzip', '.gz']:
        compression = CompressionType.GZIP
    else:
        compression = CompressionType.none

    binary_signs = {'.hsb', '.bin', '.pickle'}
    binary_signs = binary_signs.intersection(path.suffixes)
    if binary_signs:
        binary_pickle = True
    else:
        binary_pickle = False

    return binary_pickle, compression


def read_input_file(file: Path) -> List[HsnapRecord]:
    try:
        file = file.resolve(strict=True)
    except FileNotFoundError as e:
        log.exception("Unable to resolve source file %s", e.filename)
        raise e

    binary_pickle, compression = input_file_type_heuristic(file)
    opener = opener_based_on_compression_flag(compression)
    if binary_pickle:
        raise NotImplemented("Reading pickled files not implemented yet")
    else:
        with opener(file, 'rt', encoding='utf8') as input_file:
            records = []
            for line in input_file:
                deserialized = deserialize(line)
                records.append(deserialized)
        return records


class OutputSink:

    def __init__(self, file: Optional[Path] = None, binary_pickle=False, compression=None):
        """
        Context manager for writing HsnapRecords to file/stdout

        :param file: Output file, stdout used if None
        :param binary_pickle: Store as pickled List[HsnapRecord] rather than text file
        :param compression: Compression applied on output file
        """

        self._file = file
        self._binary = bool(binary_pickle)
        if self._binary:
            self._buffer = []  # we need a complete the list before pickling it
        self._compression = CompressionType(compression)

    def __enter__(self):
        if self._file is None:
            log.debug("Output to stdout")
            if self._compression != CompressionType.none:
                NotImplemented('Compressed output into stdout not supported')
            if self._binary:
                self._output_stream = sys.stdout.buffer
            else:
                self._output_stream = sys.stdout
        else:
            log.debug("Opening output file %s", self._file)
            opener = opener_based_on_compression_flag(self._compression)
            if self._binary:
                self._output_stream = opener(self._file, 'wb')
            else:
                self._output_stream = opener(self._file, 'wt', encoding='utf-8')
        return self

    def write(self, hsnap_record: HsnapRecord):
        if self._binary:
            self._buffer.append(hsnap_record)
        else:
            serialized = serialize(hsnap_record)
            self._output_stream.write(serialized)
            self._output_stream.write('\n')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._binary:
            pickle.dump(self._buffer, self._output_stream)
        if self._file:
            self._output_stream.close()
