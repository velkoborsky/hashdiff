import pytest
import pickle

from hashdiff.common import HsnapRecord
from hashdiff.hsnap import SCRIPT_NAME
from hashdiff.hsnap.hsnap import cli_main
from hashdiff.serialize import hex2bin


def test_hsnap_black_box_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, '-h'])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err == "")
    assert (out.startswith("usage:"))


def test_hsnap_black_box_samples_basic(monkeypatch, samples_dir, capsys, samples_references):
    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, '-f', '-', str(samples_dir / 'basic')])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()

    assert (err == "")

    out_lines = out.split('\n')
    out_records = [line.split('\t') for line in out_lines if line]
    output = set(
        [HsnapRecord(path, int(size), float(mtime), hex2bin(hash)) for (hash, size, mtime, path) in out_records])

    expected = set((samples_references['basic']))

    assert (output == expected)


def test_hsnap_black_box_incremental(monkeypatch, samples_dir, tmpdir, capsys):
    basic_out = tmpdir / 'out.hsnap.xz'

    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, '-f', str(basic_out), '--xz', str(samples_dir / 'basic'), '-v'])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err)
    assert (err.startswith("Scanning for files"))
    err_lines = err.split('\n')
    assert ('Processed files: 3' in err_lines)
    assert (out == '')
    assert (basic_out.exists())

    monkeypatch.setattr('sys.argv',
                        [SCRIPT_NAME, '-i', str(basic_out), '-f', '-', str(samples_dir / 'incremental'), '-v'])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err)
    err_lines = err.split('\n')
    assert ('Incremental: 2 reused, 1 different, 1 new' in err_lines)


def test_hsnap_black_box_pickle(monkeypatch, samples_dir, tmpdir, capsys, samples_references):
    sample_name = 'basic'
    pickled_out = tmpdir / 'out.hsb'

    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, '-f', str(pickled_out), str(samples_dir / sample_name), '--pickle'])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err == "")
    assert (out == "")
    assert (pickled_out.exists())

    with pickled_out.open('rb') as f:
        results = pickle.load(f)
    assert type(results) is list
    assert len(results) == 3
    assert type(results[0]) is HsnapRecord

    records = set((results))
    expected = set((samples_references[sample_name]))
    assert (records == expected)
