"""
Parse to and from a Excel format for isotherms.

The _parser_version variable documents any changes to the format,
and is used to check for any deprecations.

This is based on work by Paul Iacomi (https://raw.githubusercontent.com/pauliacomi/pyGAPS/master/src/pygaps/parsing/excel.py)

"""


import pandas
import xlrd
from adsorption_file_parser import logger
from xlrd.xldate import xldate_as_datetime


_parser_version = "1.0"

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
        headers = []
        dtypes = {}
        experiment_data = {}
        while header_col < sht.ncols:
            header = sht.cell(header_row, header_col).value
            if header == '':
                break
            # read header, data, and dtype
            headers.append(header)
            experiment_data[header] = [
                sht.cell(i, header_col).value for i in range(start_row, final_row)
            ]
            # read the data type
            # only read the data type if it is not a pressure, loading or branch
            if header_col > 2:
                dtype = sht.cell(header_row - 1, header_col).value
                if dtype != '':
                    dtypes[header] = dtype
            header_col += 1
        data = pandas.DataFrame(experiment_data)
        data = data.astype(dtypes)

        # process isotherm branches if they exist
        if 'branch' in data.columns:
            data['branch'] = data['branch'].apply(lambda x: 0 if x == 'ads' else 1)
        else:
            raw_dict['branch'] = 'guess'
    meta = {}
    # read the secondary isotherm parameters
    if 'metadata' in wb.sheet_names():
        sht = wb.sheet_by_name('metadata')
        row_index = 0
        while row_index < sht.nrows:
            namec = sht.cell(row_index, 0)
            valc = sht.cell(row_index, 1)
            if namec.ctype == xlrd.XL_CELL_EMPTY:
                break
            if valc.ctype == xlrd.XL_CELL_BOOLEAN:
                val = bool(valc.value)
            elif valc.ctype == xlrd.XL_CELL_EMPTY:
                val = None
            else:
                val = valc.value
            if namec.value == '_exptl_date':
                val = xldate_as_datetime(valc.value, sht.book.datemode).isoformat()
            meta[namec.value] = val
            row_index += 1

    version = meta.pop("_parser_version", None)
    if not version or float(version) < float(_parser_version):
        logger.warning(
            f"The file version is {version} while the parser uses version {_parser_version}. "
            "Strange things might happen, so double check your data."
        )

    data_dict = {'pressure' : data['pressure'].to_list(), 'loading' : data['loading'].to_list(), 'branch' : data['branch'].to_list()}
    return meta, data_dict