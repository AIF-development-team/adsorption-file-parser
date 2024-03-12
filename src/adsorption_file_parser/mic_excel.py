# -*- coding: utf-8 -*-
"""Parse Micromeritics Excel(.xls) report files."""

from itertools import product

import xlrd

from adsorption_file_parser import logger
from adsorption_file_parser.utils import common_utils as util
from adsorption_file_parser.utils import unit_parsing

_META_DICT = {
    'material': {
        'text': ('sample:', 'echantillon:'),
        'type': 'string',
        'xl_ref': (0, 1),
    },
    'adsorbate': {
        'text': ('analysis ads', ),
        'type': 'string',
        'xl_ref': (0, 1),
    },
    'temperature': {
        'text': ('analysis bath', ),
        'type': 'numeric',
        'xl_ref': (0, 1),
    },
    'operator': {
        'text': ('operator', 'analyste'),
        'type': 'string',
        'xl_ref': (0, 1),
    },
    'date': {
        'text': ('started', ),
        'type': 'datetime',
        'xl_ref': (0, 1),
    },
    'date_finished': {
        'text': ('completed', ),
        'type': 'datetime',
        'xl_ref': (0, 1),
    },
    'date_report': {
        'text': ('report time', ),
        'type': 'datetime',
        'xl_ref': (0, 1),
    },
    'material_mass': {
        'text': ('sample mass', ),
        'type': 'numeric',
        'xl_ref': (0, 1),
    },
    'comment': {
        'text': ('comments', ),
        'type': 'string',
        'xl_ref': (0, 0),
    },
    'error': {
        'text': ('primary data', ),
        'type': 'error',
        'xl_ref': (1, 0),
    },
}

_DATA_DICT = {
    'pressure': {
        'text': ('absolute', ),
    },
    'pressure_saturation': {
        'text': ('saturation', ),
    },
    'pressure_relative': {
        'text': ('relative', ),
    },
    'time_total': {
        'text': ('elapsed time', ),
    },
    'loading': {
        'text': ('quantity', ),
    },
}


def parse(path):
    """
    Parse an xls file generated by micromeritics software.

    Parameters
    ----------
    path: str
        Path to the file to be read.

    Returns
    -------
    meta : dict
        Isotherm metadata.
    data : dict
        Isotherm data.
    """
    meta = {}
    data = {}
    errors = []

    # open the workbook
    workbook = xlrd.open_workbook(path, encoding_override='latin-1')
    try:
        sheet = workbook.sheet_by_name("Isotherm Tabular Report")
    except Exception:
        sheet = workbook.sheet_by_index(0)

    # local for efficiency
    meta_dict = _META_DICT.copy()

    # iterate over all cells in the notebook
    for row, col in product(range(sheet.nrows), range(sheet.ncols)):

        # check if empty
        cell_value = sheet.cell(row, col).value
        if not isinstance(cell_value, str) or cell_value == '':
            continue

        # check if we are in the data section
        if cell_value not in ['Isotherm Tabular Report', 'Isotherm Linear Absolute Plot']:
            cell_value = cell_value.strip().lower()
            try:
                key = util.search_key_starts_def_dict(cell_value, meta_dict)
            except StopIteration:
                continue

            ref = meta_dict[key]['xl_ref']
            tp = meta_dict[key]['type']

            val = sheet.cell(row + ref[0], col + ref[1]).value
            if val == '':
                meta[key] = None
            elif tp == 'numeric':
                val = val.replace(',', '.')  # bad way of dealing with french locale
                nb, unit = unit_parsing.parse_number_unit_string(val)
                meta[key] = nb
                meta[f'{key}_unit'] = unit
            elif tp == 'string':
                if key == 'operator' and val == 'XXXX':
                    continue
                meta[key] = util.handle_excel_string(val)
            elif tp == 'datetime':
                meta[key] = util.handle_string_date(val)
            elif tp == 'date':
                meta[key] = util.handle_xlrd_date(val, sheet)
            elif tp == 'time':
                meta[key] = util.handle_xlrd_time(val, sheet)
            elif tp == 'timedelta':
                meta[key] = val
            elif tp == 'error':
                errors += _parse_errors(sheet, row, col)

            del meta_dict[key]  # delete for efficiency

        else:  # If "data" section

            header_list = _get_header(sheet, row, col)
            head, units = _parse_header(header_list)  # header
            meta.update(units)

            for i, h in enumerate(head[1:]):
                points = _parse_data(sheet, row, col + i)

                if h == 'time_total':
                    data[h] = list(map(util.handle_string_time_minutes, points[1:]))
                elif h == 'pressure_saturation':
                    data[h] = [float(x) for x in points[1:]]
                elif h.startswith('pressure') or h.startswith('loading'):
                    print(h)
                    data[h] = [float(x) for x in points]
                else:
                    data[h] = points

    if errors:
        meta['errors'] = errors

    _check(meta, data, path)

    # Set extra metadata
    if meta.get('comment'):
        meta['comment'] = meta['comment'].replace('Comments: ', '')
    if not meta.get('operator'):
        meta['operator'] = None

    # Get instrument from absolute position
    meta['apparatus'] = str(sheet.cell(1, 0).value)
    meta['apparatus_details'] = str(sheet.cell(2, 1).value)

    return meta, data


def _get_header(sheet, row, col):
    """Locate all column labels for data collected during the experiment."""
    final_column = col
    header_row = 2
    # Abstract this sort of thing
    header = sheet.cell(row + header_row, final_column).value.lower()
    header_options = []
    for option in _DATA_DICT.values():
        header_options.extend(option['text'])
    while any(header.startswith(label) for label in header_options):
        final_column += 1
        if final_column > sheet.ncols - 1:
            break
        header = sheet.cell(row + header_row, final_column).value.lower()

    if col == final_column:
        print('yes')
        # this means no header exists, can happen in some older files
        # the units might not be standard! TODO should check
        logger.warning('Default data headers supplied for file.')
        return [
            'Relative Pressure (P/Po)',
            'Absolute Pressure (kPa)',
            'Quantity Adsorbed (cm³/g STP)',
            'Elapsed Time (h:min)',
            'Saturation Pressure (kPa)',
        ]

    return [sheet.cell(row + header_row, i).value for i in range(col, final_column)]


def _parse_header(header_split):
    """Parse an adsorption/desorption header to get columns and units."""
    headers = ['branch']
    units = {}

    for h in header_split:
        try:
            text = h.lower()
            header = util.search_key_starts_def_dict(text, _DATA_DICT)
        except StopIteration:
            header = h

        headers.append(header)

        if header == 'loading':
            unit_string = util.RE_BETWEEN_BRACKETS.search(h).group().strip()
            unit_dict = unit_parsing.parse_loading_string(unit_string)
            units.update(unit_dict)
            units["original_loading_string"
                  ] = unit_string  # TODO discuss unit parsing within AIF group

        elif header == 'pressure':
            unit_string = util.RE_BETWEEN_BRACKETS.search(h).group().strip()
            unit_dict = unit_parsing.parse_pressure_string(unit_string)
            units.update(unit_dict)
            units["original_pressure_string"
                  ] = unit_string  # TODO discuss unit parsing within AIF group

    if 'pressure' not in headers:
        if 'pressure_relative' in headers:
            headers[headers.index('pressure_relative')] = 'pressure'
            units['pressure_mode'] = 'relative'
            units['pressure_unit'] = None

    return headers, units


def _parse_data(sheet, row, col):
    """Return all collected data points for a given column."""
    rowc = 3
    # Data can start on two different rows. Try first option and then next row.
    if sheet.cell(row + rowc, col).value:
        start_row = row + rowc
        final_row = row + rowc
    else:
        start_row = row + (rowc + 1)
        final_row = row + (rowc + 1)
    point = sheet.cell(final_row, col).value
    while point:
        final_row += 1
        if final_row > sheet.nrows - 1:
            break
        point = sheet.cell(final_row, col).value
        # sometimes 1-row gaps are left for P0 measurement
        if not point:
            final_row += 1
            if final_row > sheet.nrows - 1:
                break
            point = sheet.cell(final_row, col).value
    return [
        sheet.cell(i, col).value for i in range(start_row, final_row) if sheet.cell(i, col).value
    ]


def _parse_errors(sheet, row, col):
    """
    Look for all cells that contain errors.
    (are below a cell labelled primary data).
    """
    ref = _META_DICT['error']['xl_ref']
    val = sheet.cell(row + ref[0], col + ref[1]).value
    if not val:
        return []
    final_row = row + ref[0]
    error = sheet.cell(final_row, col + ref[1]).value
    while error:
        final_row += 1
        error = sheet.cell(final_row, col + ref[1]).value
    return [sheet.cell(i, col + ref[1]).value for i in range(row + ref[0], final_row)]


def _check(meta, data, path):
    """
    Check keys in data and logs a warning if a key is empty.
    Also logs a warning for errors found in file.
    """
    if 'loading' in data:

        # Some files use an odd format
        # We instead remove unreadable values
        dels = []
        for k, v in data.items():
            if not v:
                logger.info(f'No data collected for {k} in file {path}.')

            if len(v) != len(data['pressure']):
                dels.append(k)

        for d in dels:
            del data[d]

    if 'errors' in meta:
        logger.warning('Report file contains warnings:')
        logger.warning('\n'.join(meta['errors']))


meta, data = parse('tests/data/problems/ASAP-001-314-report.XLS')
print(data)