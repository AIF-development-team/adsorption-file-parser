# -*- coding: utf-8 -*-
"""Units and interconversion."""

_MOLAR_UNITS = {
    'mmol': 0.001,
    'mol': 1,
    'kmol': 1000,
    'cm3(STP)': 4.461e-5,
    'mL(STP)': 4.461e-5,
    'cc(STP)': 4.461e-5,
    'L(STP)': 4.461e-2,
}
_MASS_UNITS = {
    'amu': 1.66054e-27,
    'mg': 0.001,
    'cg': 0.01,
    'dg': 0.1,
    'g': 1,
    'kg': 1000,
}
_VOLUME_UNITS = {
    'cm3': 1,
    'mL': 1,
    'cc': 1,
    'dm3': 1e3,
    'L': 1e3,
    'm3': 1e6,
}
_PRESSURE_UNITS = {
    'Pa': 1,
    'kPa': 1000,
    'MPa': 1000000,
    'mbar': 100,
    'bar': 100000,
    'atm': 101325,
    'mmHg': 133.322,
    'torr': 133.322,
}
_TEMPERATURE_UNITS = {
    'K': -273.15,
    '°C': 273.15,
}
