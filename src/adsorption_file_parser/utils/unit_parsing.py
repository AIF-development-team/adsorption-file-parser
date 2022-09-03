# -*- coding: utf-8 -*-
"""Parses the most common unit types."""

import re

from adsorption_file_parser import ParsingError
from adsorption_file_parser import logger
from adsorption_file_parser.utils import common_utils as util
from adsorption_file_parser.utils.units import _MASS_UNITS
from adsorption_file_parser.utils.units import _MOLAR_UNITS
from adsorption_file_parser.utils.units import _VOLUME_UNITS

# [pattern, substitution value]
pre_proc_sub = [
    # quotes, underscores, commas
    [util.RE_PUNCTUATION, ''],
    # single spaces/tabs
    [util.RE_SPACES, ' '],
    # unicode superscripts
    [util.RE_SUPERSCRIPT2, '2'],
    [util.RE_SUPERSCRIPT3, '3'],
    # remove all brackets
    [util.RE_BRACKETS, ''],
]

# the string can be a single descriptor like "wt%" or "fraction volume"
ALIAS_FRACTION = {
    'percent': ('%', 'percent'),
    'fraction': ('fractional', 'fraction', 'frac'),
}
ALIAS_BASIS = {
    'mass': ('mass', 'wt', 'weight'),
    'molar': ('molar', 'mol'),
    'volume': ('volume', 'vol'),
}
ALIAS_PRESSURE_UNIT = {
    'torr': ('mmhg', 'torr', 'mm hg'),
    'Pa': ('pa', 'pascal'),
    'kPa': ('kpa', 'kilopascal'),
    'MPa': ('mpa', 'megapascal'),
    'bar': ('bar', ),
    'mbar': ('mbar', 'millibar'),
    'atm': ('atm', 'atmosphere'),
}
ALIAS_VOLUME_UNIT = {
    'cm3': ('cm3', 'cc'),
    'mL': ('ml', ),
    'dm3': ('dm3', ),
    'L': ('l', ),
    'm3': ('m3', ),
}


def parse_number_unit_string(string):
    """Split a string """
    number, unit = string.strip().split()
    number = float(util.RE_ONLY_NUMBERS.search(string.replace(',', '')).group())
    return number, unit


def parse_temperature_unit(text: str) -> str:
    """Ensure celsius is correctly written."""
    lower_text = text.lower()
    if 'c' in lower_text:
        return '°C'
    if 'k' in lower_text:
        return 'K'
    return text


def parse_temperature_string(temperature_string: str) -> str:
    """Correctly format a temperature string."""

    # first clean the string
    temperature_string_clean = clean_string(temperature_string, pre_proc_sub)
    # then correctly format degC/degK
    temperature_string_clean = parse_temperature_unit(temperature_string_clean)

    return temperature_string_clean


def parse_pressure_string(pressure_string: str) -> str:
    """Correctly parse a pressure string."""

    final_units = {
        'pressure_mode': None,
        'pressure_unit': None,
    }

    # first clean the string
    pressure_string_clean = clean_string(pressure_string, pre_proc_sub)

    if pressure_string_clean in ['relative', 'p/p0']:
        final_units['pressure_mode'] = 'relative'
    elif pressure_string_clean == 'relative%':
        final_units['pressure_mode'] = 'relative%'
    else:
        final_units['pressure_mode'] = 'absolute'
        for p_unit, p_text in ALIAS_PRESSURE_UNIT.items():
            if any(text == pressure_string_clean for text in p_text):
                final_units['pressure_unit'] = p_unit

        if not final_units['pressure_unit']:
            raise ParsingError(f'Cannot understand pressure units in {pressure_string}')

    return final_units


def upper_litre(text: str) -> str:
    """Have the litre capitalized."""
    return text[:-1] + text[-1].upper() if text in ['ml', 'l'] else text


def clean_string(text: str, patterns: 'list[str]') -> str:
    """Apply a list of regex substitution patterns."""
    for pattern in patterns:
        text = re.sub(pattern[0], pattern[1], text)
    return text.lower().strip()


def find_loading_basis(loading_unit):
    """Find the loading basis from the unit"""
    if loading_unit in _MOLAR_UNITS:
        return 'molar'
    if loading_unit in _MASS_UNITS:
        return 'mass'
    if loading_unit in _VOLUME_UNITS:
        logger.warning(
            f"The loading unit '{loading_unit}' is ambiguous. "
            'It can mean either gas at STP, gas at isotherm temperature '
            'or liquid volume. Here we assumed it is gas at isotherm temperature. '
            'DOUBLE CHECK if this is the case !!!'
        )
        return 'volume_gas'
    raise ParsingError(f"Cannot understand loading units in '{loading_unit}'.")


def find_material_basis(material_unit):
    """Find the material basis from the unit"""
    if material_unit in _MASS_UNITS:
        return 'mass'
    if material_unit in _VOLUME_UNITS:
        return 'volume'
    if material_unit in _MOLAR_UNITS:
        return 'molar'
    raise ParsingError(f"Cannot understand material units in '{material_unit}'.")


def parse_loading_string(loading_string: str, missing_units: dict = None) -> 'tuple[str, str]':
    """
    Correctly parse an adsorption loading unit string.

    Loading strings come in many flavours depending on the
    source, instrument manufacturer, world location etc.

    However they should always be either in
    [amount adsorbed] / [material quantity]
    or in a fractional/percentage amount adsorbed.
    """
    final_units = {
        'loading_basis': None,
        'loading_unit': None,
        'material_basis': None,
        'material_unit': None,
    }
    if missing_units:
        final_units.update(missing_units)
    error_text = 'Isotherm cannot be parsed due to loading string format.'

    # first clean the string
    loading_string_clean = clean_string(loading_string, pre_proc_sub)

    # the string can be a single descriptor like "wt%" or "fractional volume"
    for lbasis, lbtext in ALIAS_FRACTION.items():
        if any(text in loading_string_clean for text in lbtext):
            final_units['loading_basis'] = lbasis

            for mbasis, mbtext in ALIAS_BASIS.items():
                if any(text in loading_string_clean for text in mbtext):
                    final_units['material_basis'] = mbasis

                    return final_units
            raise ParsingError(error_text)

    # the string can also be a combined descriptor like "mmol/g" or "cm3 g^-1"

    # first check for "stp" moniker, removing it if true
    stp = False
    if 'stp' in loading_string_clean:
        stp = True
        final_units['loading_basis'] = 'molar'
        loading_string_clean = re.sub(r'stp', '', loading_string_clean)
        loading_string_clean = re.sub(r'\s+', ' ', loading_string_clean).strip()

    # now, this string could be as "x/y" or "x y-1"
    unit_components = loading_string_clean.split('/')
    if len(unit_components) != 2:
        unit_components = loading_string_clean.split(' ')
        unit_components[1] = unit_components[1].replace('-1', '')
    if len(unit_components) != 2:
        raise ParsingError(error_text)

    loading_unit, material_unit = map(str.strip, unit_components)

    # we standardize some units
    loading_unit, material_unit = map(upper_litre, (loading_unit, material_unit))

    # We add the STP moniker in a standard way
    if stp:
        loading_unit = loading_unit + '(STP)'

    final_units['loading_basis'] = find_loading_basis(loading_unit)
    final_units['loading_unit'] = loading_unit

    final_units['material_basis'] = find_material_basis(material_unit)
    final_units['material_unit'] = material_unit

    return final_units
