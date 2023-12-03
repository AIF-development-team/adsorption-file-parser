# -*- coding: utf-8 -*-
"""Tests 3P excel parsing."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_3P_XL
from .conftest import DATA_3P_XML
from .conftest import RECREATE


class Test3P():
    """Test parsing of 3p files"""
    @pytest.mark.parametrize('path', DATA_3P_XL)
    def test_read_excel_3p(self, path):
        """Test reading of 3P report files."""
        meta, data = afp.read(path=path, manufacturer='3p', fmt='xl')
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json

    @pytest.mark.parametrize('path', DATA_3P_XML)
    def test_read_xml_3p(self, path):
        """Test reading of 3P xml (.jwgbt) files."""
        # TODO cannot be parsed - read comment in 'trp_xlm'

        # meta, data = afp.read(path=path, manufacturer='3p', fmt='jwgbt')
        # result_dict = {'meta': meta, 'data': data}
        # json_path = path.with_suffix('.json')

        # if RECREATE:
        #     with open(json_path, 'w', encoding='utf8') as file:
        #         json.dump(result_dict, file, indent=4)

        # with open(json_path, 'r', encoding='utf8') as file:
        #     result_dict_json = json.load(file)

        # assert result_dict == result_dict_json
