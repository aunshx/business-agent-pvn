import json
import uuid

from fastapi import APIRouter

from app.schemas import Anomaly, QueryRequest, QueryResponse
from app.services import anomalies, dataset
from app.services.executor import derive_chart_spec, execute_plan
from app.services.planner import plan_query

router = APIRouter()


@router.get("/schema")
def get_schema():
    return dataset.get_schema_summary()


@router.get("/anomalies", response_model=list[Anomaly])
def list_anomalies():
    return anomalies.get_anomalies()


@router.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    request_id = uuid.uuid4().hex[:12]
    plan = request.plan_override if request.plan_override is not None else plan_query(request.question, request_id)
    df = execute_plan(plan)
    chart_spec = derive_chart_spec(df, plan)
    rows = json.loads(df.to_json(orient="records"))
    return QueryResponse(
        plan=plan,
        rows=rows,
        row_count=df.attrs.get("row_count", len(df)),
        truncated=df.attrs.get("truncated", False),
        chart_spec=chart_spec,
        request_id=request_id,
    )
