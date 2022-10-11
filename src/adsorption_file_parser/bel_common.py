# -*- coding: utf-8 -*-
"""Common BEL file utilities."""

import dateutil.parser

import adsorption_file_parser.utils.common_utils as util
from adsorption_file_parser import logger
from adsorption_file_parser.utils import unit_parsing

_META_DICT = {
    'material': {
        'text': ('comment1', 'コメント１'),
        'type': 'string',
        'xl_ref': (0, 2),
    },
    'adsorbate': {
        'text': ('adsorptive', '吸着質名称'),
        'type': 'string',
        'xl_ref': (0, 2),
    },
    'temperature': {
        'text': (
            'adsorption temperature',
            'adsorption temperature',
            'meas. temp.',
            '吸着温度',
        ),
        'type': 'numeric',
        'unit': 'temperature_unit',
        'xl_ref': (0, 2),
    },
    'operator': {
        'text': ('comment2', 'コメント２'),
        'type': 'string',
        'xl_ref': (0, 2),
    },
    'date': {
        'text': ('date of measurement', '測定日'),
        'type': 'datetime',
        'xl_ref': (0, 2),
    },
    'material_mass': {
        'text': ('sample weight', 'サンプル質量'),
        'unit': 'material_mass_unit',
        'type': 'numeric',
        'xl_ref': (0, 2),
    },
    'measurement_duration': {
        'text': ('time of measurement', '測定時間'),
        'type': 'timedelta',
        'xl_ref': (0, 2),
    },
    'serialnumber': {
        'text': ('serial number', 's/n', 'instrument', 'シリアルナンバー', '装置ｓ／ｎ'),
        'type': 'string',
        'xl_ref': (0, 2),
    },
    'errors': {
        'text': ('primary data', ),
        'type': 'error',
        'xl_ref': (0, 2),
    },
    'comment3': {
        'text': ('comment3', 'コメント３'),
        'type': 'string',
        'xl_ref': (0, 2),
    },
    'comment4': {
        'text': ('comment4', 'コメント４'),
        'type': 'string',
        'xl_ref': (0, 2),
    },
    'cell_volume': {
        'text': ('vs/', 'standard volume'),
        'type': 'numeric',
        'unit': 'cell_volume_unit',
        'xl_ref': (0, 2),
    },
    'dead_volume': {
        'text': ('dead volume', ),
        'type': 'numeric',
        'xl_ref': (0, 2),
    },
    'equilibration_time': {
        'text': ('equilibrium time', '平衡時間'),
        'type': 'numeric',
        'unit': 'equilibration_time_unit',
        'xl_ref': (0, 2),
    },
}

_DATA_DICT = {
    'measurement': {
        'text': ('no', ),
    },
    'pressure_internal': {
        'text': ('pi/', ),
    },
    'pressure': {
        'text': ('pe/', ),
    },
    'pressure2': {
        'text': ('pe2/', ),
    },
    'pressure_saturation': {
        'text': ('p0/', ),
    },
    'pressure_relative': {
        'text': ('p/p0', ),
    },
    'dead_volume': {
        'text': ('vd/', ),
    },
    'loading': {
        'text': ('v/', 'va/', 'n/', 'na/'),
    },
}


def _parse_header(header_split):
    """Parse an adsorption/desorption header to get columns and units."""
    headers = ['branch']
    units = {}

    for h in header_split:
        try:
            text = h.replace(' ', '').lower()
            header = util.search_key_starts_def_dict(text, _DATA_DICT)
        except StopIteration:
            header = h

        headers.append(header)

        if header == 'loading':
            unit_string = h.split('/')[1].strip()
            unit_dict = unit_parsing.parse_loading_string(unit_string)
            units.update(unit_dict)
            units["original_loading_string"
                  ] = unit_string  # TODO discuss unit parsing within AIF group

        elif header == 'pressure':
            unit_string = h.split('/')[1].strip()
            unit_dict = unit_parsing.parse_pressure_string(unit_string)
            units.update(unit_dict)
            units["original_pressure_string"
                  ] = unit_string  # TODO discuss unit parsing within AIF group

    return headers, units


def _handle_bel_date(text):
    return dateutil.parser.parse(text, yearfirst=True).isoformat()


def _check(meta, data, path):
    """
    Check keys in data and logs a warning if a key is empty.

    Also logs a warning for errors found in file.
    """
    if 'loading' in data:
        empties = (k for k, v in data.items() if not v)
        for empty in empties:
            logger.info(f'No data collected for {empty} in file {path}.')
    if 'errors' in meta:
        logger.warning('\n'.join(meta['errors']))
