# -*- coding: utf-8 -*-
"""Parse Quantachrome .raw files."""
# TODO:
# - check unit of equilibration time
# - check if pressure is always in bar

import datetime

import adsorption_file_parser.utils.common_utils as util


def parse(path):
    """
    Get the isotherm and sample data from a Quantachrome .raw file.

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

    # Parse header
    # Some files use ':' and some use '=' as separator; both are handled below.
    # 'GAS TYPE' and 'GASTYPE' are both observed in the wild.
    with open(path, 'r', encoding='utf8', errors='ignore') as raw_file:
        for counter, line in enumerate(raw_file):
            line = line.rstrip('\r\n')
            if line.startswith('SAMPLE ID'):
                meta['material'] = '_'.join(line.split()[2:])
            elif line.startswith('SAMPLE WEIGHT'):
                sep = ':' if ':' in line else '='
                meta['material_mass'] = float(line.split(sep)[1].split()[0])
                meta['material_unit'] = 'g'
            elif line.startswith('P/Po TOLERANCE'):
                sep = ':' if ':' in line else '='
                meta['pressure_tolerance'] = line.split(sep)[1].strip()
            elif line.startswith('EQUILIBRATION TIME'):
                sep = ':' if ':' in line else '='
                meta['equilibration_time'] = line.split(sep)[1].strip()
            elif line.startswith('ANALYSIS TIME'):
                sep = ':' if ':' in line else '='
                meta['measurement_duration'] = float(line.split(sep)[1].split()[0])
                meta['measurement_duration_unit'] = 'min'
            elif line.startswith('GAS TYPE') or line.startswith('GASTYPE'):
                sep = ':' if ':' in line else '='
                meta['adsorbate'] = line.split(sep)[1].strip()
            elif line.startswith('CROSS-SECTIONAL AREA'):
                sep = ':' if ':' in line else '='
                meta['cross_sectional_area'] = float(line.split(sep)[1].split()[0])
                meta['cross_sectional_area_unit'] = 'A^2'
            elif line.startswith('MOLECULAR WEIGHT'):
                sep = ':' if ':' in line else '='
                meta['adsorbate_molecular_weight'] = float(line.split(sep)[1].split()[0])
                meta['adsorbate_molecular_weight_unit'] = 'g/mol'
            elif line.startswith('NONIDEALITY CORR FACTOR'):
                sep = ':' if ':' in line else '='
                meta['adsorbate_non_ideality'] = float(line.split(sep)[1].split()[0])
                meta['adsorbate_non_ideality_unit'] = 'Torr^-1'
            elif line.strip() == '':
                header_end = counter
                break

    # Parse data table
    with open(path, 'r', encoding='utf8', errors='ignore') as raw_file:
        for counter, line in enumerate(raw_file):
            if counter == header_end + 1:
                table_header = line.replace(',', '').split()
            elif counter > header_end and line.strip() == '':
                data_end = counter
                break
            elif counter > header_end + 1:
                data.append(line.split())

    # Normalise table header tokens to canonical key names
    _HEADER_MAP = {
        0: {'P/Po': 'pressure_relative'},
        1: {'VOLUME': 'loading'},
        2: {'(cc)': 'pressure_tolerance', '(CC)': 'pressure_tolerance'},
        3: {'P/Po': 'equilibration_time'},
        4: {'TOLERANCE': 'isotherm_type'},
    }
    for i, entry in enumerate(table_header):
        if i in _HEADER_MAP and entry in _HEADER_MAP[i]:
            table_header[i] = _HEADER_MAP[i][entry]

    data = dict(zip(table_header, map(lambda *x: list(x), *data)))

    # Convert numeric columns from strings to float
    _NUMERIC = {'pressure_relative', 'loading', 'pressure_tolerance', 'equilibration_time'}
    for col in _NUMERIC:
        if col in data:
            data[col] = [float(v) for v in data[col]]

    # Parse footer
    with open(path, 'r', encoding='utf8', errors='ignore') as raw_file:
        for counter, line in enumerate(raw_file):
            if counter > data_end:
                line = line.rstrip('\r\n')
                if line.startswith('DATE'):
                    date_str = ' '.join(line.split()[1:]).lstrip(':').strip()
                    for fmt in ('%a %b %d %H:%M:%S %Y', '%m/%d/%y', '%m/%d/%Y'):
                        try:
                            date = datetime.datetime.strptime(date_str, fmt)
                            meta['date'] = util.handle_string_date(date.strftime('%Y-%m-%d %H:%M:%S'))
                            break
                        except ValueError:
                            continue
                elif line.startswith('ANALYSIS TEMPERATURE') or line.startswith('BATH TEMPERATURE'):
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
