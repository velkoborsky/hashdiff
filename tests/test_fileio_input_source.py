import pytest

from hashdiff.fileio import InputSource

# noinspection PyUnresolvedReferences
from common_fixtures import samples_dir, samples_references


def test_input_source_files(samples_dir, samples_references):
    source_files = list((samples_dir / 'input_source').glob('*'))
    assert len(source_files)

    expected = set((samples_references['basic']))

    for file in source_files:
        with InputSource(file) as input_source:
            records = set(input_source)
            assert records == expected


def test_input_source_stdin(samples_dir, samples_references, monkeypatch):
    source_files = list((samples_dir / 'input_source').glob('*'))
    assert len(source_files)

    expected = set((samples_references['basic']))

    for file in source_files:
        monkeypatch.setattr('sys.stdin', file.open('rt', encoding='utf-8'))
        with InputSource() as input_source:
            records = set(input_source)
            assert records == expected
