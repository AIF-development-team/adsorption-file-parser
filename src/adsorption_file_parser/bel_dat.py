"""Interface with BEL-generated DAT files."""

import dateutil.parser
from adsorption_file_parser.utils.bel_common import _META_DICT
from adsorption_file_parser.utils.bel_common import _parse_header
from adsorption_file_parser import ParsingError

from adsorption_file_parser.utils import common_utils as util
from adsorption_file_parser.utils import unit_parsing


def parse(path):
    """
    Get the isotherm and sample data from a BEL Japan .dat file.
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
    head = []
    data = []

    # local for efficiency
    meta_dict = _META_DICT.copy()

    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            values = line.strip().split(sep='\t')
            nvalues = len(values)

            if nvalues == 2:  # If value pair
                text, val = [v.strip('"').replace(',', ' ') for v in values]
                text = text.lower()
                try:  # find the standard name in the metadata dictionary
                    key = util.search_key_starts_def_dict(text, meta_dict)
                except StopIteration:  # Store unknown as is
                    key = text.replace(" ", "_")
                    key_units = key.split("/")
                    if key_units == 2:
                        key = key_units[0]
                        val = val + " " + key_units[1]
                    meta[key] = val
                    continue

                meta[key] = val
                del meta_dict[key]  # delete for efficiency

                if text == "temperature":
                    text, unit = key.split("/")
                    meta['temperature_unit'] = unit_parsing.parse_temperature_unit(unit)

            elif nvalues < 2:  # If "section title"
                title = values[0].strip().lower()

                # read "adsorption" section
                if title.startswith('adsorption data'):
                    file.readline()  # ====== - discard
                    header_line = file.readline().rstrip()  # header
                    header_list = header_line.replace('"', '').split("\t")
                    head, units = _parse_header(header_list)  # header
                    meta.update(units)

                    line = file.readline()  # first ads line
                    while not line.startswith('0'):
                        data.append([0] + list(map(float, line.split())))
                        line = file.readline()

                # read "desorption" section
                elif title.startswith('desorption data'):
                    file.readline()  # ====== - discard
                    file.readline()  # header - discard

                    line = file.readline()  # first des line
                    while not line.startswith('0'):
                        data.append([1] + list(map(float, line.split())))
                        line = file.readline()

                else:  # other section titles
                    continue

            else:
                raise ParsingError(f"Unknown line format: {line}")

    # Format extra metadata
    meta['date'] = dateutil.parser.parse(meta['date']).isoformat()
    meta['apparatus'] = 'BEL ' + meta["serialnumber"]

    # Prepare data
    data = dict(zip(head, map(lambda *x: list(x), *data)))

    return meta, data
