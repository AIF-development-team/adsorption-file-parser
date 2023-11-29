# -*- coding: utf-8 -*-
"""Tests SMS DVS excel file parsing."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_SMS_DVS_XL
from .conftest import RECREATE


class TestSMS_DVS():
    """Test parsing of SMS DVS files"""
    @pytest.mark.parametrize('path', DATA_SMS_DVS_XL)
    def test_read_excel_smsdvs(self, path):
        """Test reading of SMS DVS excel processed files."""
        meta, data = afp.read(path=path, manufacturer='smsdvs', fmt='xlsx')
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json
