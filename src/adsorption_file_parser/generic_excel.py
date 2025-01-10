"""
Parse to and from a Excel format for isotherms.

This is based on work by Paul Iacomi (https://raw.githubusercontent.com/pauliacomi/pyGAPS/master/src/pygaps/parsing/excel.py)
"""

import xlrd

from adsorption_file_parser.utils import common_utils as util

_META_DICT = {
    'isotherm_data': {
        'text': ('Isotherm type', ),
        'name': 'isotherm_data',
        'row': 0,
        'column': 0,
    },
}


def parse(path):
    """
    Load an isotherm from a pyGAPS Excel file.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the excel file.

    """

    # isotherm type (point/model)

    raw_dict = {}

    # Get excel workbook and sheet
    wb = xlrd.open_workbook(path)
    if 'data' in wb.sheet_names():
        sht = wb.sheet_by_name('data')
    else:
        sht = wb.sheet_by_index(0)

    # read the main isotherm parameters
    for field in _META_DICT.values():
        valc = sht.cell(field['row'], field['column'] + 1)
        if valc.ctype == xlrd.XL_CELL_EMPTY:
            val = None
        else:
            val = valc.value
        raw_dict[field['name']] = val

    # find data/model limits
    type_row = _META_DICT['isotherm_data']['row']

    # development for data type
    if sht.cell(type_row, 1).value.lower().startswith('data'):

        # Store isotherm type

        header_row = type_row + 1
        start_row = header_row + 1
        final_row = start_row

        while final_row < sht.nrows:
            point = sht.cell(final_row, 0).value
            if point == '':
                break
            final_row += 1

        # read the data in
        header_col = 0
        head = []
        data = {}

        while header_col < sht.ncols:
            header = sht.cell(header_row, header_col).value
            if header == '':
                break
            # read header, data, and dtype
            head.append(header)
            data[header] = [sht.cell(i, header_col).value for i in range(start_row, final_row)]
            # read the data type
            # only read the data type if it is not a pressure, loading or branch
            if header_col > 2:
                dtype = sht.cell(header_row - 1, header_col).value
                if dtype != '':
                    data = [util.cast_string(s) for s in data]
            header_col += 1

        # process isotherm branches if they exist
        for col in data:
            if col == 'branch':
                data['branch'] = [0 if s == 'ads' else 1 for s in data['branch']]
            else:
                data[col] = [float(s) for s in data[col]]

    # read the secondary isotherm metadata
    meta = {}
    if 'metadata' in wb.sheet_names():
        sht = wb.sheet_by_name('metadata')
        row_index = 0
        while row_index < sht.nrows:
            namec = sht.cell(row_index, 0)
            valc = sht.cell(row_index, 1)
            if valc.value is None:
                val = None
            elif valc.ctype is xlrd.XL_CELL_EMPTY:
                val = None
            elif valc.ctype is xlrd.XL_CELL_NUMBER:
                val = valc.value
            elif valc.ctype is xlrd.XL_CELL_TEXT:
                val = util.handle_excel_string(valc.value)
            elif valc.ctype is xlrd.XL_CELL_DATE:
                val = util.handle_xlrd_datetime(valc.value, sht)

            meta[namec.value] = val
            row_index += 1

    return meta, data
