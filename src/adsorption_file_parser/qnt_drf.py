# -*- coding: utf-8 -*-
"""Parse Quantachrome .drf files."""
# TODO:
# - check unit of equilibration time
# - check if pressure is always in bar

import datetime

import adsorption_file_parser.utils.common_utils as util


def parse(path):
    """
    Get the isotherm and sample data from a Quantachrome .drf file.

    Parameters
    ----------
    path : str
        Path to the file to be read.

    Returns
    -------
    meta : dict
        Isotherm metadata.
    data : dict
        Isotherm data.
    """

    meta = {}
    data = []

    # Parse header (all separators are ':' in .drf files)
    with open(path, 'r', encoding='utf8', errors='ignore') as drf_file:
        for counter, line in enumerate(drf_file):
            line = line.rstrip('\r\n')
            if line.startswith('SAMPLE ID'):
                meta['material'] = '_'.join(line.split()[2:])
            elif line.startswith('SAMPLE WEIGHT'):
                meta['material_mass'] = float(line.split(':')[1].strip())
                meta['material_unit'] = 'g'
            elif line.startswith('P/Po TOLERANCE'):
                meta['pressure_tolerance'] = line.split(':')[1].strip()
            elif line.startswith('EQUILIBRATION TIME'):
                meta['equilibration_time'] = line.split(':')[1].strip()
            elif line.startswith('ANALYSIS TIME'):
                meta['measurement_duration'] = float(line.split(':')[1].split()[0])
                meta['measurement_duration_unit'] = 'min'
            elif line.startswith('GAS TYPE'):
                meta['adsorbate'] = line.split(':')[1].strip()
            elif line.startswith('CROSS-SECTIONAL AREA'):
                meta['cross_sectional_area'] = float(line.split(':')[1].split()[0])
                meta['cross_sectional_area_unit'] = 'A^2'
            elif line.startswith('MOLECULAR WEIGHT'):
                meta['adsorbate_molecular_weight'] = float(line.split(':')[1].split()[0])
                meta['adsorbate_molecular_weight_unit'] = 'g/mol'
            elif line.startswith('NONIDEALITY CORR FACTOR'):
                meta['adsorbate_non_ideality'] = float(line.split(':')[1].split()[0])
                meta['adsorbate_non_ideality_unit'] = 'Torr^-1'
            elif line.strip() == '':
                header_end = counter
                break

    # Parse data table
    with open(path, 'r', encoding='utf8', errors='ignore') as drf_file:
        for counter, line in enumerate(drf_file):
            if counter == header_end + 1:
                table_header = line.replace(',', '').split()
            elif counter > header_end and line.strip() == '':
                data_end = counter
                break
            elif counter > header_end + 1:
                data.append(line.split())

    # Normalise table header tokens to canonical key names
    _HEADER_MAP = {
        0: {'P': 'pressure'},
        1: {'Po': 'pressure_saturation', 'P0': 'pressure_saturation'},
        2: {'Volume(cc)': 'loading', 'VOLUME(cc)': 'loading'},
        3: {'P/Po-TOL.': 'pressure_tolerance'},
        4: {'EQ-TIME': 'equilibration_time'},
        5: {'TIME': 'measurement_time'},
    }
    for i, entry in enumerate(table_header):
        if i in _HEADER_MAP and entry in _HEADER_MAP[i]:
            table_header[i] = _HEADER_MAP[i][entry]

    data = dict(zip(table_header, map(lambda *x: list(x), *data)))

    # Convert numeric columns from strings to float
    _NUMERIC = {'pressure', 'pressure_saturation', 'loading',
                'pressure_tolerance', 'equilibration_time', 'measurement_time'}
    for col in _NUMERIC:
        if col in data:
            data[col] = [float(v) for v in data[col]]

    # Derive relative pressure from absolute P and P0 recorded at each point
    data['pressure_relative'] = [
        round(float(p) / float(data['pressure_saturation'][0]), 6)
        for p in data['pressure']
    ]

    # Parse footer
    with open(path, 'r', encoding='utf8', errors='ignore') as drf_file:
        for counter, line in enumerate(drf_file):
            if counter > data_end:
                line = line.rstrip('\r\n')
                if line.startswith('ENDRUN'):
                    date_str = ' '.join(line.split()[1:])
                    date = datetime.datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                    meta['end_of_run'] = util.handle_string_date(date.strftime('%Y-%m-%d %H:%M:%S'))
                elif line.startswith('DATE'):
                    date_str = ' '.join(line.split()[1:])
                    date = datetime.datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                    meta['date'] = util.handle_string_date(date.strftime('%Y-%m-%d %H:%M:%S'))
                elif line.startswith('ANALYSIS TEMPERATURE'):
                    meta['temperature'] = line.split(':')[1].strip()
                elif line.startswith('SAMPLE DESC'):
                    meta['material_description'] = line.split(':')[1].strip()
                elif line.startswith('AMBIENT TEMPERATURE'):
                    meta['ambient_temperature'] = line.split(':')[1].strip()

    # Normalise units so consumers (e.g. pyGAPS) don't have to guess
    from adsorption_file_parser.utils import unit_parsing
    meta['loading_unit'] = 'cc(STP)'
    meta['loading_basis'] = unit_parsing.find_loading_basis('cc(STP)')  # 'molar'
    meta['material_basis'] = unit_parsing.find_material_basis(meta['material_unit'])
    if 'temperature' in meta:
        meta['temperature'] = float(meta['temperature'])
    meta['temperature_unit'] = 'K'
    if 'adsorbate' in meta:
        meta['adsorbate'] = meta['adsorbate'].strip().lower()

    return meta, data
