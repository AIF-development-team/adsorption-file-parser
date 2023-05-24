# -*- coding: utf-8 -*-
"""Tests Micromeritics excel parsing."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_MIC_XL
from .conftest import RECREATE


class TestMicromeritics():
    """Test parsing of Micromeritics files."""
    @pytest.mark.parametrize('path', DATA_MIC_XL)
    def test_read_excel_mic(self, path):
        """Test reading of micromeritics report files."""
        meta, data = afp.read(path=path, manufacturer='mic', fmt='xl')
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json
