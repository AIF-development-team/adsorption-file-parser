# -*- coding: utf-8 -*-
import re

import dateutil.parser

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


def handle_string_numeric(text):
    """Convert to a int/float."""
    if isinstance(text, str):
        try:
            return int(text)
        except ValueError:
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
