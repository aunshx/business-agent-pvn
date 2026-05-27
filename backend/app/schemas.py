from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ColumnName = Literal[
    "Agency",
    "Agy",
    "Vendor",
    "Category",
    "SubCategory",
    "Object",
    "Subobj",
    "FMonth",
    "Amount",
]

ChartType = Literal["bar", "line", "table", "single_number"]


class FilterOp(BaseModel):
    column: ColumnName
    op: Literal["equals", "contains", "in", "gt", "lt", "gte", "lte"]
    value: Any


class GroupAgg(BaseModel):
    group_by: list[ColumnName]
    agg_column: Literal["Amount"]
    agg_func: Literal["sum", "mean", "count", "max", "min"]


class QueryPlan(BaseModel):
    interpretation: str
    filters: list[FilterOp] = Field(default_factory=list)
    grouping: GroupAgg | None = None
    sort_by: str | None = None
    sort_desc: bool = True
    limit: int | None = None
    chart_hint: ChartType
    confidence: Literal["high", "medium", "low"]
    notes: str | None = None


class QueryRequest(BaseModel):
    question: str
    plan_override: QueryPlan | None = None


class ChartSpec(BaseModel):
    type: ChartType
    x: str | None = None
    y: str | None = None
    series: str | None = None


class QueryResponse(BaseModel):
    plan: QueryPlan
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool = False
    chart_spec: ChartSpec
    request_id: str


class Anomaly(BaseModel):
    title: str
    description: str
    suggested_question: str
    severity: Literal["info", "notable", "high"]
