# -*- coding: utf-8 -*-
import ast
import re

import dateutil.parser

from adsorption_file_parser import ParsingError
from adsorption_file_parser import logger

# regexes

RE_PUNCTUATION = re.compile(r"['\"_,\^]")  # quotes, underscores, commas, superscript
RE_SPACES = re.compile(r'\s+')  # spaces/tabs
# unicode superscripts
RE_SUPERSCRIPT2 = re.compile('²')
RE_SUPERSCRIPT3 = re.compile('³')
RE_BRACKETS = re.compile(r'[\{\[\(\)\]\}]')  # all bracket type

RE_ONLY_NUMBERS = re.compile(r'^(-)?\d+(.|,)?\d+')
RE_BETWEEN_BRACKETS = re.compile(r'(?<=\().+?(?=\))')


def search_key_in_def_dict(key, def_dict):
    """Finds key in the dictionary, provided it exists in the value ["text"] list"""
    return next(k for k, v in def_dict.items() if any(key == n for n in v.get('text', [])))


def search_key_starts_def_dict(key, def_dict):
    """Finds key in the dictionary, provided it starts in the value ["text"] list"""
    return next(k for k, v in def_dict.items() if any(key.startswith(n) for n in v.get('text', [])))


def _is_none(s: str) -> bool:
    """Check if a value is a text None."""
    if not s:
        return True
    if s.lower() == 'none':
        return True
    return False


def _is_bool(s: str) -> bool:
    """Check a value is a text bool."""
    if s.lower() in ['true', 'false']:
        return True
    return False


def _from_bool(s: str) -> bool:
    """Convert a string into a boolean."""
    if s.lower() == 'true':
        return True
    if s.lower() == 'false':
        return False
    raise ValueError('String cannot be converted to bool')


def _is_int(s: str) -> bool:
    """Check if a value is a int."""
    try:
        int(s)
        return True
    except ValueError:
        return False


def _is_float(s: str) -> bool:
    """Check if a value is a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_list(s: str) -> bool:
    """Check a value is a simple list."""
    if s.startswith('[') and s.endswith(']'):
        return True
    return False


def _from_list(s: str):
    """Convert a value into a list/tuple/dict."""
    # note that the function will fail if the list has other spaces
    return ast.literal_eval(s.replace(' ', ","))


def cast_string(s):
    """Check and cast strings of various data types."""
    if _is_none(s):
        return None
    if _is_bool(s):
        return _from_bool(s)
    if s.isnumeric():
        return int(s)
    if _is_int(s):
        return int(s)
    if _is_float(s):
        return float(s)
    if _is_list(s):
        return _from_list(s)
    if isinstance(s, str):
        return s
    raise ParsingError(f"Could not parse value '{s}'")


def handle_string_numeric(text):
    """Convert string to an int or a float."""
    if isinstance(text, str):
        if _is_int(text):
            return int(text)
        else:
            return float(text)
    return text


def handle_string_date(text):
    """Convert general date string to ISO format."""
    try:
        return dateutil.parser.parse(text).isoformat()
    except dateutil.parser.ParserError:
        if '午' in text:
            text = text.replace('下午', '')
            text = text.replace('上午', '')
            return handle_string_date(text)
        logger.warning(f"Could not parse date '{text}'")
        return text


def handle_xlrd_datetime(text, sheet):
    """Convert datetime cell from xlrd to ISO format."""
    from xlrd.xldate import xldate_as_datetime
    return xldate_as_datetime(text, sheet.book.datemode).isoformat()


def handle_xlrd_date(text, sheet):
    """Convert date cell from xlrd to a simple format."""
    from xlrd.xldate import xldate_as_datetime
    return xldate_as_datetime(text, sheet.book.datemode).strftime('%Y-%m-%d')


def handle_xlrd_time(text, sheet):
    """Convert time cell from xlrd to a simple format."""
    from xlrd.xldate import xldate_as_datetime
    return xldate_as_datetime(text, sheet.book.datemode).strftime('%H:%M:%S')


def handle_xlrd_timedelta(text, sheet):
    """Convert timedelta cell from xlrd (in h) to a string."""
    from xlrd.xldate import xldate_as_tuple
    dt = xldate_as_tuple(text, sheet.book.datemode)
    return f'{dt[3]}:{dt[4]}:{dt[5]}'


def handle_excel_string(text):
    """
    Replace any newline found.

    Input is a cell of type 'string'.
    """
    if text:
        return str(text).replace('\r\n', ' ')
    return None


def handle_string_time_minutes(text):
    """Convert time points from HH:MM format to minutes."""
    hours, mins = str(text).split(':')
    return int(hours) * 60 + int(mins)
