import pytest
import os
from pathlib import Path, PurePosixPath

from hashdiff.hcmp import SCRIPT_NAME
from hcmp.hcmp import cli_main


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


def test_hcmp_black_box_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, '-h'])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err == "")
    assert (out.startswith('usage: hcmp'))


def test_hcmp_black_box_run(samples_dir, monkeypatch, capsys):
    hcmp_samples_dir = samples_dir / 'hcmp'
    f1 = hcmp_samples_dir / 'basic.hsn'
    f2 = hcmp_samples_dir / 'incremental.hsn'
    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, str(f1), str(f2)])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err == "")
    assert out == ('Deleted (no copy left): 0\n'
                   '\n'
                   'Deleted duplicates (some copies left): 0\n'
                   '\n'
                   'Changed (same path, different file): 1\n'
                   'hello\n'
                   '\n'
                   'Moved (same file, different path): 0\n'
                   '\n'
                   'Added (new files): 1\n'
                   'def.txt\n'
                   '\n'
                   'Added duplicates (of previously existing): 0\n')

