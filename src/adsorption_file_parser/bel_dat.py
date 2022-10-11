# -*- coding: utf-8 -*-
"""Parse BEL DAT files."""

from adsorption_file_parser import ParsingError
from adsorption_file_parser.bel_common import _META_DICT
from adsorption_file_parser.bel_common import _handle_bel_date
from adsorption_file_parser.bel_common import _parse_header
from adsorption_file_parser.utils import common_utils as util
from adsorption_file_parser.utils import unit_parsing


def parse(path, lang='ENG') -> "tuple[dict, dict]":
    """
    Get the isotherm and sample data from a BEL Japan .dat file.

    Parameters
    ----------
    path : str
        Path to the file to be read.
    lang : str
        Language encoding of the file, either 'ENG' or 'JPN'.

    Returns
    -------
    meta : dict
        Isotherm metadata.
    data : dict
        Isotherm data.
    """

    # set encoding
    if lang == 'ENG':
        encoding = 'cp1252'
    elif lang == 'JPN':
        encoding = 'shift_jis'
    else:
        raise ParsingError("Unknown language/encoding option.")

    meta = {}
    head = []
    data = []

    # local for efficiency
    meta_dict = _META_DICT.copy()

    with open(path, 'r', encoding=encoding) as file:
        for line in file:
            values = line.strip().split(sep='\t')
            nvalues = len(values)

            if nvalues == 2:  # If value pair
                text, val = [v.strip('"').replace(',', ' ') for v in values]
                text = text.lower()
                try:  # find the standard name in the metadata dictionary
                    key = util.search_key_starts_def_dict(text, meta_dict)
                except StopIteration:  # Store unknown as is
                    key, unit = _handle_bel_dat_string_units(text)
                    if unit:
                        val = val + ' ' + unit
                    meta[key] = val
                    continue

                tp = meta_dict[key]['type']
                unit_key = meta_dict[key].get('unit')
                del meta_dict[key]  # delete for efficiency

                if val == '':
                    meta[key] = None
                elif tp == 'numeric':
                    meta[key] = util.handle_string_numeric(val)
                elif tp == 'string':
                    meta[key] = val
                elif tp in ['date', 'datetime']:
                    meta[key] = _handle_bel_date(val)
                elif tp == 'time':
                    meta[key] = val
                elif tp == 'timedelta':
                    meta[key] = val

                if unit_key:
                    text, unit = _handle_bel_dat_string_units(text)
                    if key == 'temperature':
                        meta[unit_key] = unit_parsing.parse_temperature_unit(unit)
                    else:
                        meta[unit_key] = unit

            elif nvalues < 2:  # If "section title"
                title = values[0].strip().lower()

                # read "adsorption" section
                if title in ['adsorption data', '吸着データ']:
                    file.readline()  # ====== - discard
                    header_line = file.readline().rstrip()  # header
                    header_list = header_line.replace('"', '').split('\t')
                    head, units = _parse_header(header_list)  # header
                    meta.update(units)

                    line = file.readline()  # first ads line
                    while not line.startswith('0'):
                        data.append([0] + list(map(float, line.split())))
                        line = file.readline()

                # read "desorption" section
                elif title in ['desorption data', '脱着データ']:
                    file.readline()  # ====== - discard
                    file.readline()  # header - discard

                    line = file.readline()  # first des line
                    while not line.startswith('0'):
                        data.append([1] + list(map(float, line.split())))
                        line = file.readline()

                else:  # other section titles
                    continue

            else:
                raise ParsingError(f'Unknown line format: {line}')

    # Format extra metadata
    meta['apparatus'] = 'BEL ' + meta['serialnumber']

    # Prepare data
    data = dict(zip(head, map(lambda *x: list(x), *data)))

    return meta, data


def _handle_bel_dat_string_units(text):
    # TODO find a more elegant way of replacing JIS characters
    text = text.replace("／", "/")
    text = text.replace("：", ":")
    text = text.replace("ｋ", "k")
    #
    key = text.replace(':', '').replace(' ', '_')
    key_units = key.split('/')
    if len(key_units) == 2:
        return key_units[0], key_units[1]
    return key, None
