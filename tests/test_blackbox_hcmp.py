import pytest

from hashdiff.hcmp import SCRIPT_NAME
from hashdiff.hcmp.hcmp import cli_main


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

