from pathlib import Path

import pytest

import fileio
from hstool import SCRIPT_NAME
from hstool.hstool import cli_main

# noinspection PyUnresolvedReferences
from common_fixtures import samples_dir, samples_references


def test_hstool_black_box_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, '-h'])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()
    assert (err == "")
    assert (out.startswith('usage: hstool'))


def test_hstool_black_box_filter_defaults(samples_dir, monkeypatch, capsys, tmpdir):
    in_file = samples_dir / 'hstool' / 'hashdiff.hsn'

    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, 'filter', '-p', '.*__main__\\.py'])

    with in_file.open('rt') as in_stream:
        monkeypatch.setattr('sys.stdin', in_stream)
        with pytest.raises(SystemExit) as e:
            cli_main()
        out, err = capsys.readouterr()

    assert err == ""

    out_lines = [l for l in out.split('\n') if l]
    assert len(out_lines) == 3
    assert all(x.endswith('__main__.py') for x in out_lines)


def test_hstool_black_box_filter_split_to_file(samples_dir, monkeypatch, capsys, tmpdir):
    in_file = samples_dir / 'hstool' / 'hashdiff.hsn'
    matched_out = Path(tmpdir) / 'matched_out.hsn'
    not_matched_out = Path(tmpdir) / 'not_matched_out.hsn'

    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, 'filter',
                                     '--input', str(in_file),
                                     '--pattern', 'hsnap',
                                     '--matched', str(matched_out),
                                     '--not-matched', str(not_matched_out)])
    with pytest.raises(SystemExit) as e:
        cli_main()
    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""

    matched = fileio.read_input_file(matched_out)
    not_matched = fileio.read_input_file(not_matched_out)

    assert len(matched) > 0
    assert all([x.path.startswith('hsnap') for x in matched])

    assert len(not_matched) > 0
    assert not any([x.path.startswith('hsnap') for x in not_matched])


def test_hstool_black_box_ls_defaults(samples_dir, monkeypatch, capsys):
    in_file = samples_dir / 'hstool' / 'hashdiff.hsn'

    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, 'ls'])

    with in_file.open('rt') as in_stream:
        monkeypatch.setattr('sys.stdin', in_stream)
        with pytest.raises(SystemExit) as e:
            cli_main()
        out, err = capsys.readouterr()

    assert err == ""

    out_lines = out.split('\n')
    assert out_lines == ['__init__.py', 'common.py', 'fileio.py', 'hcmp/', 'hsnap/', 'hstool/', 'humanizer.py',
                         'serialize.py', '']


def test_hstool_black_box_ls_paths(samples_dir, monkeypatch, capsys):
    in_file = samples_dir / 'hstool' / 'hashdiff.hsn'
    paths = ['hsnap', 'hcmp']

    monkeypatch.setattr('sys.argv', [SCRIPT_NAME, 'ls'] + paths)

    with in_file.open('rt') as in_stream:
        monkeypatch.setattr('sys.stdin', in_stream)
        with pytest.raises(SystemExit) as e:
            cli_main()
        out, err = capsys.readouterr()

    assert err == ""
    out_lines = out.split('\n')
    expected = ("hcmp:\n"
                "__init__.py\n"
                "__main__.py\n"
                "args.py\n"
                "compare.py\n"
                "filter.py\n"
                "hcmp.py\n"
                "normalize.py\n"
                "summary.py\n"
                "\n"
                "hsnap:\n"
                "__init__.py\n"
                "__main__.py\n"
                "args.py\n"
                "hash.py\n"
                "hsnap.py\n"
                "walk.py\n").split('\n')
    assert out_lines == expected
