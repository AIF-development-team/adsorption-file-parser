# -*- coding: utf-8 -*-
from pathlib import Path

# set to true to remake all jsons
RECREATE = False

SMSDVS_PATH = Path('./tests/data/smsdvs')
BEL_PATH = Path('./tests/data/bel')
MIC_PATH = Path('./tests/data/mic')
TP_PATH = Path('./tests/data/3p')
QNT_PATH = Path('./tests/data/qnt')

DATA_SMSDVS_XL = tuple(SMSDVS_PATH.glob('*.xlsx'))
DATA_MIC_XL = tuple(MIC_PATH.glob('*.xls'))
DATA_BEL = tuple(BEL_PATH.glob('*.DAT'))
DATA_BEL_XL = tuple(BEL_PATH.glob('*.xls'))
DATA_BEL_CSV = tuple(BEL_PATH.glob('*.csv'))
DATA_3P_XL = tuple(TP_PATH.glob('*.xlsx'))
DATA_QNT = tuple(QNT_PATH.glob('*.txt'))
