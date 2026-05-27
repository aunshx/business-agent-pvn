import pandas as pd

from app.schemas import ChartSpec, FilterOp, GroupAgg, QueryPlan
from app.services import dataset

MAX_ROWS = 1000


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _apply_mask(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    return df[mask.fillna(False)]


def apply_filter(df: pd.DataFrame, filter_op: FilterOp) -> pd.DataFrame:
    series = df[filter_op.column]
    op = filter_op.op
    value = filter_op.value
    numeric = pd.api.types.is_numeric_dtype(series)

    if op == "equals":
        if numeric:
            return _apply_mask(df, series == _to_number(value))
        return _apply_mask(df, series.astype("string").str.lower() == str(value).strip().lower())

    if op == "contains":
        return _apply_mask(
            df, series.astype("string").str.contains(str(value), case=False, na=False, regex=False)
        )

    if op == "in":
        values = value if isinstance(value, (list, tuple, set)) else [value]
        if numeric:
            return _apply_mask(df, series.isin([_to_number(v) for v in values]))
        wanted = {str(v).strip().lower() for v in values}
        return _apply_mask(df, series.astype("string").str.lower().isin(wanted))

    number = _to_number(value)
    if op == "gt":
        return _apply_mask(df, series > number)
    if op == "lt":
        return _apply_mask(df, series < number)
    if op == "gte":
        return _apply_mask(df, series >= number)
    if op == "lte":
        return _apply_mask(df, series <= number)

    return df


def apply_grouping(df: pd.DataFrame, grouping: GroupAgg) -> pd.DataFrame:
    grouped = df.groupby(grouping.group_by, dropna=False)[grouping.agg_column]
    aggregated = getattr(grouped, grouping.agg_func)()
    return aggregated.reset_index()


def apply_sort(df: pd.DataFrame, plan: QueryPlan) -> pd.DataFrame:
    if not plan.sort_by or df.empty:
        return df
    sort_col = plan.sort_by
    if sort_col not in df.columns:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(numeric_cols) == 1:
            sort_col = numeric_cols[0]
        else:
            return df
    return df.sort_values(sort_col, ascending=not plan.sort_desc, kind="stable")


def apply_limit(df: pd.DataFrame, plan: QueryPlan) -> pd.DataFrame:
    if plan.limit is not None and plan.limit >= 0:
        return df.head(plan.limit)
    return df


def execute_plan(plan: QueryPlan) -> pd.DataFrame:
    df = dataset.get_dataframe()
    for filter_op in plan.filters:
        df = apply_filter(df, filter_op)
    if plan.grouping is not None:
        df = apply_grouping(df, plan.grouping)
    df = apply_sort(df, plan)
    df = apply_limit(df, plan)

    full_count = len(df)
    truncated = full_count > MAX_ROWS
    if truncated:
        df = df.head(MAX_ROWS)
    df = df.reset_index(drop=True)
    df.attrs["row_count"] = full_count
    df.attrs["truncated"] = truncated
    return df


def derive_chart_spec(df: pd.DataFrame, plan: QueryPlan) -> ChartSpec:
    if df.empty or len(df.columns) == 0:
        return ChartSpec(type="table")

    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    categorical = [c for c in df.columns if c not in numeric]
    metric = "Amount" if "Amount" in numeric else (numeric[0] if len(numeric) == 1 else None)

    if len(df) == 1 and metric is not None:
        x = categorical[0] if len(categorical) == 1 else None
        return ChartSpec(type="single_number", x=x, y=metric)

    if "FMonth" in df.columns and metric is not None and metric != "FMonth" and len(df.columns) == 2:
        return ChartSpec(type="line", x="FMonth", y=metric)

    if len(df.columns) == 2 and len(categorical) == 1 and len(numeric) == 1:
        return ChartSpec(type="bar", x=categorical[0], y=numeric[0])

    if plan.chart_hint == "single_number" and metric is not None:
        return ChartSpec(type="single_number", y=metric)
    if plan.chart_hint == "bar" and categorical and metric is not None:
        return ChartSpec(type="bar", x=categorical[0], y=metric)
    if plan.chart_hint == "line" and "FMonth" in df.columns and metric is not None:
        return ChartSpec(type="line", x="FMonth", y=metric)

    return ChartSpec(type="table")


if __name__ == "__main__":
    import uuid

    from app.services.planner import plan_query

    questions = [
        "Top 10 vendors paid by Health Care Authority",
        "How much did Molina receive in total?",
        "Which agency spent the most on travel?",
        "What was the largest single payment in the dataset?",
        "What's interesting about Boeing?",
    ]
    for question in questions:
        plan = plan_query(question, uuid.uuid4().hex[:12])
        df = execute_plan(plan)
        spec = derive_chart_spec(df, plan)
        print("=" * 80)
        print(f"Q: {question}")
        print(f"confidence={plan.confidence}  rows={df.attrs['row_count']}  truncated={df.attrs['truncated']}")
        print(df.head(10).to_string())
        print(f"chart_spec: {spec.model_dump()}")
