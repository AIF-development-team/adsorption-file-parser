# -*- coding: utf-8 -*-
"""Tests generic CSV excel parsing."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_GENERIC_EXCEL
from .conftest import RECREATE


class TestGeneric():
    """Test parsing of generic excel files."""
    @pytest.mark.parametrize('path', DATA_GENERIC_EXCEL)
    def test_read_generic_excel(self, path):
        """Test reading of generic excel files."""
        meta, data = afp.read(path=path, manufacturer='generic', fmt='xls')
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json
