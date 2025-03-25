# -*- coding: utf-8 -*-
"""Tests guessing of file format and manufacturer."""

import json

import pytest

import adsorption_file_parser as afp

from .conftest import DATA_MIC_XL
from .conftest import DATA_BEL
from .conftest import DATA_BEL_XL
from .conftest import DATA_BEL_CSV
from .conftest import DATA_3P_XL
from .conftest import DATA_3P_XML
from .conftest import DATA_QNT
from .conftest import DATA_SMS_DVS_XL
from .conftest import DATA_GENERIC_CSV
from .conftest import DATA_GENERIC_EXCEL


class TestGuessFormat():
    """Test guessing of file formats"""
    @pytest.mark.parametrize('path', DATA_MIC_XL)
    def test_guess_mic_xl(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('mic', 'xl')

    @pytest.mark.parametrize('path', DATA_BEL)
    def test_guess_bel_dat(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('bel', 'dat')

    @pytest.mark.parametrize('path', DATA_BEL_XL)
    def test_guess_bel_xl(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('bel', 'xl')

    @pytest.mark.parametrize('path', DATA_BEL_CSV)
    def test_guess_bel_csv(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('bel', 'csv')

    @pytest.mark.parametrize('path', DATA_3P_XL)
    def test_guess_3p_xl(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('3p', 'xl')

    @pytest.mark.parametrize('path', DATA_QNT)
    def test_guess_qnt(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('qnt', 'txt-raw')

    @pytest.mark.parametrize('path', DATA_SMS_DVS_XL)
    def test_guess_sms_dvs_xl(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('smsdvs', 'xlsx')

    @pytest.mark.parametrize('path', DATA_GENERIC_CSV)
    def test_guess_generic_csv(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('generic', 'csv')

    @pytest.mark.parametrize('path', DATA_GENERIC_EXCEL)
    def test_guess_generic_excel(self, path):
        manu, fmt = afp.guess_manufacturer_fmt(path=path)
        assert (manu, fmt) == ('generic', 'xls')

    @pytest.mark.parametrize('path', DATA_QNT)
    def test_read_qnt_txt(self, path):
        """Test reading of Quantachrome txt files by guessing their format."""
        meta, data = afp.read(path=path)
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json
