# -*- coding: utf-8 -*-
"""Tests various BEL file read."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_BEL
from .conftest import DATA_BEL_CSV
from .conftest import DATA_BEL_XL
from .conftest import RECREATE


class TestBEL():
    """Test parsing of BEL files"""

    @pytest.mark.parametrize('path', DATA_BEL)
    def test_read_bel_dat(self, path, tmp_path):
        """Test reading of a BEL data file."""
        lang = 'ENG'
        if path.stem.endswith('_jis'):
            lang = 'JPN'
        meta, data = afp.read(path=path, manufacturer='bel', fmt='dat', lang=lang)
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json

        aif_path = path.with_suffix('.aif')
        if RECREATE:
            afp.write_aif(aif_path, meta, data)

        # test against aif
        aif_new_path = tmp_path / path.with_suffix('.aif').name
        afp.write_aif(aif_path, meta, data)
        with open(aif_new_path, 'r', encoding='utf8') as written_file:
            written_content = written_file.read()

        with open(aif_path, 'r', encoding='utf8') as original_file:
            original_content = original_file.read()

        assert written_content == original_content

    @pytest.mark.parametrize('path', DATA_BEL_CSV)
    def test_read_bel_csv(self, path, tmp_path):
        """Test reading of BEL CSV files."""
        lang = 'ENG'
        if path.stem.endswith('_jis'):
            lang = 'JPN'
        meta, data = afp.read(path=path, manufacturer='bel', fmt='csv', lang=lang)
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json

        aif_path = path.with_suffix('.aif')
        if RECREATE:
            afp.write_aif(aif_path, meta, data)

        # test against aif
        aif_new_path = tmp_path / path.with_suffix('.aif').name
        afp.write_aif(aif_path, meta, data)
        with open(aif_new_path, 'r', encoding='utf8') as written_file:
            written_content = written_file.read()

        with open(aif_path, 'r', encoding='utf8') as original_file:
            original_content = original_file.read()

        assert written_content == original_content

    @pytest.mark.parametrize('path', DATA_BEL_XL)
    def test_read_bel_excel(self, path, tmp_path):
        """Test reading of BEL report files."""
        meta, data = afp.read(path=path, manufacturer='bel', fmt='xl')
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json

        aif_path = path.with_suffix('.aif')
        if RECREATE:
            afp.write_aif(aif_path, meta, data)

        # test against aif
        aif_new_path = tmp_path / path.with_suffix('.aif').name
        afp.write_aif(aif_path, meta, data)
        with open(aif_new_path, 'r', encoding='utf8') as written_file:
            written_content = written_file.read()

        with open(aif_path, 'r', encoding='utf8') as original_file:
            original_content = original_file.read()

        assert written_content == original_content
