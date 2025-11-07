# -*- coding: utf-8 -*-
"""Tests Quantachrome txt file parsing."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_QNT
from .conftest import RECREATE


class TestQuantachrome():
    """Test parsing of Quantachrome files"""

    @pytest.mark.parametrize('path', DATA_QNT)
    def test_read_qnt_txt(self, path, tmp_path):
        """Test reading of Quantachrome txt files."""
        meta, data = afp.read(path=path, manufacturer='qnt', fmt='txt-raw')
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
