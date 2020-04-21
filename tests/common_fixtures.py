import pytest
import os
from pathlib import Path, PurePosixPath
from hashdiff.common import HsnapRecord
from hashdiff.serialize import hex2bin


@pytest.fixture()
def samples_dir():
    test_dir = Path(os.path.abspath(__file__))
    samples_dir = test_dir.parent / "samples"
    fix_mtimes(samples_dir)
    return samples_dir


def fix_mtimes(samples_dir):
    """
    Updates sample file mtimes to those expected in reference outputs (mtimes not preserved by git)
    """
    with (samples_dir / 'reference_mtimes').open('rt') as reference_mtimes:
        for line in reference_mtimes:
            path, ref_mtime_str = line.strip().split()
            full_path = samples_dir / PurePosixPath(path)
            ref_mtime = int(ref_mtime_str)
            curr_mtime = full_path.stat().st_mtime_ns
            if curr_mtime != ref_mtime:
                print("Updating modification time on ", full_path)
                os.utime(full_path, ns=(ref_mtime, ref_mtime))


@pytest.fixture()
def samples_references(samples_dir):
    reference_files = list((samples_dir / 'reference').glob('*.ref'))
    references = {}
    for file in reference_files:
        records = []
        lines = file.read_text(encoding="utf8").split("\n")
        for line in lines:
            if not line:
                continue
            digest, size, mtime, name = line.split("\t", maxsplit=3)
            h_record = HsnapRecord(path=name, size=int(size), mtime=float(mtime), digest=hex2bin(digest))
            records.append(h_record)
        references[file.stem] = records
    return references
