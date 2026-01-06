# -*- coding: utf-8 -*-
"""Tests RASPA simulation output parsing."""
import json
import pytest
from adsorption_file_parser.sim_raspa import (
    parse_single_component,
    parse_multicomponent,
    parse_widom,
    write_single_component_aif,
    write_multicomponent_aif,
    write_widom_aif,
    detect_mode,
)
from .conftest import DATA_RASPA_SINGLE, DATA_RASPA_MULTICOMPONENT, DATA_RASPA_WIDOM
from .conftest import RECREATE


class TestRaspaSingleComponent():
    """Test parsing of single-component RASPA GCMC outputs."""

    @pytest.mark.parametrize('path', DATA_RASPA_SINGLE)
    def test_read_raspa_single(self, path):
        """Test reading of single-component RASPA simulation files."""
        mode = detect_mode(path)
        assert mode == "single"

        df = parse_single_component(path)
        result_dict = {
            'meta': {
                'operator': df['operator'].iloc[0],
                'framework_name': df['framework_name'].iloc[0],
                'adsorbate_name': df['adsorbate_name'].iloc[0],
                'adsorbate_definition': df['adsorbate_definition'].iloc[0],
                'ff_definition': df['ff_definition'].iloc[0],
                'temperature': df['temperature'].iloc[0],
                'code': df['code'].iloc[0],
            },
            'data': {
                'pressure': df['pressure'].tolist(),
                'loading': df['loading'].tolist(),
                'loading_error': df['loading_error'].tolist(),
                'excess_loading': df['excess_loading'].tolist(),
                'excess_loading_error': df['excess_loading_error'].tolist(),
                'enthalpy': df['enthalpy'].tolist(),
                'enthalpy_error': df['enthalpy_error'].tolist(),
            }
        }

        json_path = path / 'expected_single.json'
        aif_path = path / 'output_single.aif'

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)
            

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        write_single_component_aif(df, str(aif_path))
        assert aif_path.exists()
        assert result_dict == result_dict_json


class TestRaspaMulticomponent():
    """Test parsing of multicomponent RASPA GCMC outputs."""

    @pytest.mark.parametrize('path', DATA_RASPA_MULTICOMPONENT)
    def test_read_raspa_multicomponent(self, path):
        """Test reading of multicomponent RASPA simulation files."""
        mode = detect_mode(path)
        assert mode == "multicomponent"

        df_long, comp_names, fractions, definitions = parse_multicomponent(path)
        result_dict = {
            'meta': {
                'operator': df_long['operator'].iloc[0],
                'framework': df_long['framework'].iloc[0],
                'ff': df_long['ff'].iloc[0],
                'temperature': df_long['temperature'].iloc[0],
                'code': df_long['code'].iloc[0],
                'comp_names': comp_names,
                'fractions': fractions,
                'definitions': definitions,
            },
            'data': {
                'pressure': df_long['pressure'].tolist(),
                'adsorbate': df_long['adsorbate'].tolist(),
                'loading': df_long['loading'].tolist(),
                'loading_err': df_long['loading_err'].tolist(),
            }
        }

        json_path = path / 'expected_multicomponent.json'
        aif_path = path / 'output_multicomponent.aif'

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        write_multicomponent_aif(df_long, comp_names, fractions, definitions, str(aif_path))

        assert result_dict == result_dict_json
        assert aif_path.exists()


class TestRaspaWidom():
    """Test parsing of RASPA Widom insertion outputs."""

    @pytest.mark.parametrize('path', DATA_RASPA_WIDOM)
    def test_read_raspa_widom(self, path):
        """Test reading of RASPA Widom insertion files."""
        mode = detect_mode(path)
        assert mode == "widom"

        df = parse_widom(path)
        result_dict = {
            'meta': {
                'operator': df['operator'].iloc[0],
                'framework_name': df['framework_name'].iloc[0],
                'adsorbate_name': df['adsorbate_name'].iloc[0],
                'host_ff_definition': df['host_ff_definition'].iloc[0],
                'guest_ff_definition': df['guest_ff_definition'].iloc[0],
                'temperature': df['temperature'].iloc[0],
                'code': df['code'].iloc[0],
            },
            'data': {
                'henry': df['henry'].tolist(),
                'henry_error': df['henry_error'].tolist(),
                'enthalpy': df['enthalpy'].tolist(),
                'enthalpy_error': df['enthalpy_error'].tolist(),
            }
        }

        json_path = path / f"expected_widom{df['host_ff_definition'].iloc[0]}.json"

        if RECREATE:
            with open(json_path, 'w', encoding='utf8') as file:
                json.dump(result_dict, file, indent=4)

        with open(json_path, 'r', encoding='utf8') as file:
            result_dict_json = json.load(file)

        assert result_dict == result_dict_json

    @pytest.mark.parametrize('path', DATA_RASPA_WIDOM)
    def test_write_widom_aif(self, path):
        """Test writing of Widom insertion AIF files."""
        df = parse_widom(path)
        aif_path = path / f"expected_widom{df['host_ff_definition'].iloc[0]}.aif"
        
        write_widom_aif(df, output_file=str(aif_path))
        
        assert aif_path.exists()


class TestRaspaModeDetection():
    """Test automatic mode detection for RASPA outputs."""

    @pytest.mark.parametrize('path', DATA_RASPA_SINGLE)
    def test_detect_single_mode(self, path):
        """Test that single-component mode is correctly detected."""
        mode = detect_mode(path)
        assert mode == "single"

    @pytest.mark.parametrize('path', DATA_RASPA_MULTICOMPONENT)
    def test_detect_multicomponent_mode(self, path):
        """Test that multicomponent mode is correctly detected."""
        mode = detect_mode(path)
        assert mode == "multicomponent"

    @pytest.mark.parametrize('path', DATA_RASPA_WIDOM)
    def test_detect_widom_mode(self, path):
        """Test that Widom insertion mode is correctly detected."""
        mode = detect_mode(path)
        assert mode == "widom"