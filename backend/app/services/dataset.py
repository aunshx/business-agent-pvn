from __future__ import annotations

import pandas as pd

from app.core.config import settings

LOW_CARDINALITY_COLS = ["Category", "Object", "Subobj", "SubCategory"]
HIGH_CARDINALITY_COLS = ["Agency", "Vendor"]

FMONTH_TO_CALENDAR = {
    13: "Jul 2022",
    14: "Aug 2022",
    15: "Sep 2022",
    16: "Oct 2022",
    17: "Nov 2022",
    18: "Dec 2022",
    19: "Jan 2023",
    20: "Feb 2023",
    21: "Mar 2023",
    22: "Apr 2023",
    23: "May 2023",
    24: "Jun 2023",
}


def _load() -> pd.DataFrame:
    df = pd.read_csv(settings.data_path, low_memory=False)
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].str.strip()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    return df


_DF = _load()


def get_dataframe() -> pd.DataFrame:
    return _DF


def get_categorical_values(col: str) -> list[str]:
    if col not in _DF.columns:
        raise KeyError(f"unknown column: {col!r}")
    return sorted(_DF[col].dropna().unique().tolist())


def get_schema_summary() -> dict:
    columns = {}
    for col in _DF.columns:
        info = {
            "dtype": str(_DF[col].dtype),
            "cardinality": int(_DF[col].nunique(dropna=True)),
        }
        if col in LOW_CARDINALITY_COLS:
            info["values"] = get_categorical_values(col)
        columns[col] = info
    return {
        "row_count": int(len(_DF)),
        "fiscal_year": 2023,
        "biennium": "2021-23",
        "columns": columns,
        "fmonth_to_calendar": FMONTH_TO_CALENDAR,
    }
