import binascii
import logging

from hashdiff.common import HsnapRecord

log = logging.getLogger(__name__)


def deserialize(line: str) -> HsnapRecord:
    try:
        digest_s, size_s, mtime_s, name = line.rstrip().split("\t", maxsplit=3)
    except ValueError as e:
        log.exception("Unable to unpack line %s", line)
        raise e

    try:
        digest = hex2bin(digest_s)
    except binascii.Error as e:
        log.exception("Invalid digest %s on line %s", digest_s, line)
        raise e

    try:
        size = int(size_s)
    except ValueError as e:
        log.exception("Invalid size %s on line %s", size_s, line)
        raise e

    try:
        mtime = float(mtime_s)
    except ValueError as e:
        log.exception("Invalid modification time %s on line %s", mtime_s, line)
        raise e

    if len(name) == 0:
        log.error("Invalid empty file name on line %s", line)
        raise ValueError("invalid empty name")

    return HsnapRecord(path=name, size=size, mtime=mtime, digest=digest)


def serialize(h_record: HsnapRecord) -> str:
    return '{}\t{}\t{}\t{}'.format(bin2hex(h_record.digest), h_record.size, h_record.mtime, h_record.path)


def hex2bin(hex_ascii):
    return binascii.a2b_hex(hex_ascii)


def bin2hex(binary: bytes) -> str:
    return binascii.b2a_hex(binary).decode('ascii')
