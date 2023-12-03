"""
Parse to and from a CSV string/file format for isotherms.

The _parser_version variable documents any changes to the format,
and is used to check for any deprecations.

"""

from io import StringIO

import adsorption_file_parser.utils.common_utils as util
from adsorption_file_parser import ParsingError
from adsorption_file_parser import logger

_parser_version = "1.0"

_META_DICT = {
    'adsorbate': {
        'text': ('_exptl_adsorptive', ),
        'type': 'string',
    },
    'material': {
        'text': ('_adsnt_material_id', ),
        'type': 'string',
    },
    'temperature': {
        'text': ('_exptl_temperature', ),
        'type': 'numeric',
    },
    'material_mass': {
        'text': ('_adsnt_sample_mass', ),
        'type': 'numeric',
    },
    'outgas_time': {
        'text': ('_adsnt_degas_time', ),
        'type': 'string',
    },
    'outgas_temperature': {
        'text': ('_adsnt_degas_temperature', ),
        'type': 'numeric',
    },
    'temperature_unit': {
        'text': ('_units_temperature', ),
        'type': 'string',
    },
    'pressure_unit': {
        'text': ('_units_pressure', ),
        'type': 'string',
    },
    'material_unit': {
        'text': ('_units_mass', ),
        'type': 'string',
    },
    'loading_unit': {
        'text': ('_units_loading', ),
        'type': 'datetime',
    },
    'loading_basis': {
        'text': ('_basis_loading', ),
        'type': 'datetime',
    },
    'material_basis': {
        'text': ('_basis_material', ),
        'type': 'datetime',
    },
    'pressure_mode': {
        'text': ('_mode_pressure', ),
        'type': 'datetime',
    },
}


def parse(str_or_path, separator=','):
    """
    Load an isotherm from a CSV file.

    Parameters
    ----------
    str_or_path : str
        The isotherm in a CSV string format or a path
        to where one can be read.
    separator : str, optional
        Separator used int the csv file. Defaults to `,`.
    isotherm_parameters :
        Any other options to be overridden in the isotherm creation.

    Returns
    -------
    Isotherm
        The isotherm contained in the csv string or file.

    """
    try:
        with open(str_or_path, encoding='utf-8') as f:
            raw_csv = StringIO(f.read())
    except OSError:
        try:
            raw_csv = StringIO(str_or_path)
        except Exception as err:
            raise ParsingError(
                "Could not parse CSV isotherm. "
                "The `str_or_path` is invalid or does not exist. "
            ) from err

    meta = {}
    head = []
    data = []

    # local for efficiency
    meta_dict = _META_DICT.copy()

    # metadata section
    #
    for line in raw_csv:
        # break if we reach the end of the metadata
        if line.startswith('data') or line == "":
            break

        try:
            values = line.strip().split(sep=separator)
            key, val = values[:2]  # just in case the CSV contains empty vals
            try:
                key = util.search_key_in_def_dict(key, meta_dict)
            except StopIteration:
                if val:
                    key = key.replace(' ', '_')
                    meta[key] = val
                continue

            tp = meta_dict[key]['type']

            if tp == 'date':
                meta[key] = util.handle_string_date(val)
            else:  # assume numeric/string
                meta[key] = util.cast_string(val)

            del meta_dict[key]  # delete for efficiency

        except Exception as err:
            raise ParsingError(
                "Could not parse CSV isotherm. "
                f"The format may be wrong, check for errors in line {line}."
            ) from err

    # version check
    version = meta.pop("_parser_version", None)
    if not version or float(version) < float(_parser_version):
        logger.warning(
            f"The file version is {version} while the parser uses version {_parser_version}. "
            "Strange things might happen, so double check your data."
        )

    # data section
    #
    # data headers
    line = raw_csv.readline()
    head = [str.strip(s) for s in line.strip().split(separator)]

    # data
    line = raw_csv.readline()
    while line:
        data.append(line.strip().split(separator))
        line = raw_csv.readline()

    # pack data
    data = dict(zip(head, map(lambda *x: list(x), *data)))

    # process isotherm branches if they exist
    for col in data:
        if col == 'branch':
            data['branch'] = [0 if s == 'ads' else 1 for s in data['branch']]
        else:
            data[col] = [float(s) for s in data[col]]

    return meta, data
