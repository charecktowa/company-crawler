import sqlite3

import pandas as pd


def read_xlsx(file: str) -> pd.DataFrame:
    return list(pd.read_excel(file).itertuples(index=False, name=None))
