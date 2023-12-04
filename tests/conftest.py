# -*- coding: utf-8 -*-
from pathlib import Path

# set to true to remake all jsons
RECREATE = True

BEL_PATH = Path('./tests/data/bel')
MIC_PATH = Path('./tests/data/mic')
TP_PATH = Path('./tests/data/3p')
QNT_PATH = Path('./tests/data/qnt')
SMS_DVS_PATH = Path('./tests/data/sms_dvs')
GENERIC_PATH = Path('./tests/data/generic')

DATA_MIC_XL = tuple(MIC_PATH.glob('*.xls'))
DATA_BEL = tuple(BEL_PATH.glob('*.DAT'))
DATA_BEL_XL = tuple(BEL_PATH.glob('*.xls'))
DATA_BEL_CSV = tuple(BEL_PATH.glob('*.csv'))
DATA_3P_XL = tuple(TP_PATH.glob('*.xlsx'))
DATA_3P_XML = tuple(TP_PATH.glob('*.jwgbt'))
DATA_QNT = tuple(QNT_PATH.glob('*.txt'))
DATA_SMS_DVS_XL = tuple(SMS_DVS_PATH.glob('*.xlsx'))
DATA_GENERIC_CSV = tuple(GENERIC_PATH.glob('*.csv'))
