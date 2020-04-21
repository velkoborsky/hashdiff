import bz2
import gzip
import logging
import lzma
import pickle
import sys
from abc import ABC, abstractmethod
from contextlib import ExitStack
from enum import Enum
from io import TextIOWrapper
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
    with InputSource(file) as source:
        records = list(source)
    return records


class InputSource:

    def __init__(self,
                 file: Optional[Path] = None,
                 binary_pickle: Optional[bool] = None,
                 compression: Optional[CompressionType] = None):
        """
        :param file: Read file at specified path, None for stdin
        :param binary_pickle: force binary pickle mode (true/false), None for heuristic
        :param compression: forc compression mode, None for heuristic
        """

        if file:
            if isinstance(file, Path):
                try:
                    self._file = file.resolve(strict=True)
                except FileNotFoundError as e:
                    # log.exception("Unable to resolve source file %s", e.filename)
                    raise e
            else:
                raise ValueError()
        else:
            self._file = None

        if binary_pickle is None or isinstance(binary_pickle, bool):
            self._binary_pickle = binary_pickle
        else:
            raise ValueError()

        if compression is None or isinstance(compression, CompressionType):
            self._compression = compression
        else:
            raise ValueError()

        self._is_open = False

    # file signatures used to detect compression type
    compression_signatures = [
        (CompressionType.XZ, b'\xFD\x37\x7A\x58\x5A\x00'),
        (CompressionType.BZIP2, b'\x42\x5a\x68'),
        (CompressionType.GZIP, b'\x1f\x8b\x08')
    ]

    @classmethod
    def identify_compression_type(cls, starting_bytes: bytes) -> CompressionType:
        for (compression_type, signature) in cls.compression_signatures:
            if starting_bytes.startswith(signature):
                return compression_type
        return CompressionType.none

    # file signature to detect pickled content
    pickle_signature = b'\x80\x04'

    @classmethod
    def identify_binary_pickle(cls, starting_bytes: bytes) -> bool:
        guess = starting_bytes.startswith(cls.pickle_signature)
        return guess

    def __enter__(self):

        if self._is_open:
            raise RuntimeError("Already open")

        self._exit_stack = ExitStack().__enter__()

        # 1) open file, if necessary
        if self._file is None:
            log.debug("Input from stdin")
            binary_stream = sys.stdin.buffer
        else:
            log.debug("Opening input file %s", self._file)
            binary_stream = self._exit_stack.enter_context(open(self._file, 'rb'))

        try:
            # 2) decompress file, if necessary
            if self._compression is None:
                self._compression = self.identify_compression_type(starting_bytes=binary_stream.peek(6))

            if self._compression == CompressionType.XZ:
                binary_stream = self._exit_stack.enter_context(lzma.open(binary_stream))
            elif self._compression == CompressionType.BZIP2:
                binary_stream = self._exit_stack.enter_context(bz2.open(binary_stream))
            elif self._compression == CompressionType.GZIP:
                binary_stream = self._exit_stack.enter_context(gzip.open(binary_stream))

            # 3) unpickle or prepare for deserialization
            if self._binary_pickle is None:
                self._binary_pickle = self.identify_binary_pickle(starting_bytes=binary_stream.peek(6))

            if self._binary_pickle:
                self._records = pickle.load(binary_stream)
            else:
                self._text_stream = self._exit_stack.enter_context(TextIOWrapper(binary_stream, encoding='utf8'))

        except Exception as e:
            self._exit_stack.__exit__()
            raise e

        self._is_open = True

        return self

    def __exit__(self, *exc_details):

        if self._is_open:
            self._exit_stack.__exit__(*exc_details)
            self._is_open = False
        else:
            raise RuntimeError("Not open yet")

    def __iter__(self):

        if self._is_open:
            if self._binary_pickle:
                for h_record in self._records:
                    yield h_record
            else:
                for line in self._text_stream:
                    deserialized = deserialize(line)
                    yield deserialized
        else:
            raise RuntimeError("Not open yet")


class OutputSink(ABC):

    @abstractmethod
    def write(self, hsnap_record: HsnapRecord):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FileOutputSink(OutputSink):

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


class NullOutputSink(OutputSink):

    def write(self, hsnap_record: HsnapRecord):
        pass
