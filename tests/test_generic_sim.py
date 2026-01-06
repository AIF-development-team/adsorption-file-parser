# -*- coding: utf-8 -*-
"""Tests generic simulation file parsing."""

import json

import pytest

import adsorption_file_parser as afp
from adsorption_file_parser.generic_sim import parse_file, makeAIF

from .conftest import DATA_GENERIC_SIM
from .conftest import RECREATE


class TestGeneric():
    """Test parsing of generic files."""
    @pytest.mark.parametrize('path', DATA_GENERIC_SIM)
    def test_read_generic_sim(self, path):
        """Test reading of generic simulation files."""

        config = {
            "m_cell_amu": 1584.55,
            "asym_to_cell": 4.0,
            "saturation_pressure": 0.03166,
            "operator": "Marie Dupont",
            "adsorbate": "water",
            "temperature": 298.0,
            "temperature_unit": "K",
            "pressure_unit": "bar",
            "material_id": "MOF-303",
            "simulation_lot": "MLP/PBE+D3(BJ)",
            "citation": "10.5281/zenodo.14013757",
            "input_files": "MOF-303_water_298K_simulation_input.zip",
            "sampling_method": "TMMC-MD",
        }

        meta, data = parse_file(path, input_data=config)
        result_dict = {'meta': meta, 'data': data}
        json_path = path.with_suffix('.json')
        aif_path = path.with_suffix('.aif')

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)
            makeAIF(meta,data,aif_path)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json
