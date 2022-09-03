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
    def test_read_qnt_txt(self, path):
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
