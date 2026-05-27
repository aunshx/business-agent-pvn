import hashlib
import json
import time

import anthropic
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.schemas import QueryPlan
from app.services import dataset

MODEL = settings.planner_model
MAX_TOKENS = 2048
TOOL_NAME = "build_query_plan"

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class PlannerError(Exception):
    pass


def _build_system_prompt() -> str:
    schema = dataset.get_schema_summary()
    fmonth = schema["fmonth_to_calendar"]
    schema_for_prompt = {k: v for k, v in schema.items() if k != "fmonth_to_calendar"}
    agencies = dataset.get_categorical_values("Agency")

    example_plan = {
        "interpretation": "The 10 vendors that received the most total payment from the Social and Health Services agency, ranked by total amount paid.",
        "filters": [
            {"column": "Agency", "op": "equals", "value": "Social and Health Services"}
        ],
        "grouping": {"group_by": ["Vendor"], "agg_column": "Amount", "agg_func": "sum"},
        "sort_by": "Amount",
        "sort_desc": True,
        "limit": 10,
        "chart_hint": "bar",
        "confidence": "high",
        "notes": None,
    }

    parts = [
        "You translate plain-English questions about a Washington State vendor "
        "payments dataset into a structured query plan by calling the "
        "build_query_plan tool. You never write SQL or code. Pandas executes the "
        "plan downstream, and the plan is validated against a strict schema "
        "before anything runs, so every column name and value you choose must be "
        "exact.",
        "Dataset: Washington State vendor payments for fiscal year 2023 (biennium "
        "2021-23). There is exactly one fiscal year of data; never assume another "
        "year exists.",
        "Schema (column types, cardinality, and full value lists for the "
        "low-cardinality columns):",
        json.dumps(schema_for_prompt, indent=2),
        "Column notes: Agy is the numeric agency code and Agency is its name; "
        "Object and Subobj are short codes whose readable names are Category and "
        "SubCategory; Amount is the only column worth aggregating. Vendor names "
        "are stored in uppercase, so match a vendor with the contains op and an "
        "uppercase substring. Agency, Category, Object, Subobj, and SubCategory "
        "values must match the provided lists exactly.",
        "Agency names (101 total, match exactly):",
        json.dumps(agencies, indent=2),
        "Months are numbered by biennium position (FMonth 13-24). Use this "
        "mapping to turn a calendar phrase like 'April 2023' into an FMonth filter "
        "(April 2023 -> 22):",
        json.dumps(fmonth, indent=2),
        "Rules. Always fill interpretation with a plain-English restatement of "
        "what you understood; the user reads it and can correct it. "
        "Confidence measures how well-specified the question is, not how "
        "plausible your plan is. Use high only when the question names a concrete "
        "metric or comparison and the columns and values map cleanly onto this "
        "schema. Set confidence to low when the question is open-ended or names a "
        "subject without saying what to measure about it (for example 'what's "
        "interesting about X', 'tell me about Y', 'how is Z doing') -- you should "
        "still produce your best-guess plan, but mark it low and use notes to "
        "list the choices you had to guess (which metric, grouping, sort, or time "
        "range) and what the user should clarify. Also set confidence to low when "
        "the question references a column or value that does not exist in this "
        "dataset, and say so in notes. "
        "Pick chart_hint to fit the result shape: single_number for one value, "
        "bar for comparisons across categories, line for trends over FMonth, "
        "table for raw rows.",
        "Worked example.\nQuestion: \"Top 10 vendors paid by the Department of "
        "Social and Health Services\"\nPlan:\n" + json.dumps(example_plan, indent=2),
    ]
    return "\n\n".join(parts)


def _tool_definition() -> dict:
    return {
        "name": TOOL_NAME,
        "description": "Record the structured query plan that answers the user's question about the vendor payments dataset.",
        "input_schema": QueryPlan.model_json_schema(),
    }


def _extract_tool_use(response):
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            return block
    return None


def plan_query(question: str, request_id: str) -> QueryPlan:
    system_prompt = _build_system_prompt()
    system_prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
    system = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
    tools = [_tool_definition()]
    tool_choice = {"type": "tool", "name": TOOL_NAME}
    messages = [{"role": "user", "content": question}]

    start = time.monotonic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        tools=tools,
        tool_choice=tool_choice,
        messages=messages,
    )
    latency_ms = int((time.monotonic() - start) * 1000)

    block = _extract_tool_use(response)
    if block is not None:
        try:
            plan = QueryPlan.model_validate(block.input)
            logger.log_interaction(
                request_id, MODEL, system_prompt_hash, question,
                response.to_dict(), plan, latency_ms, "success",
            )
            return plan
        except ValidationError as exc:
            error = str(exc)
    else:
        error = "model did not return a build_query_plan tool call"

    logger.log_interaction(
        request_id, MODEL, system_prompt_hash, question,
        response.to_dict(), None, latency_ms, "failed", error,
    )

    messages.append({"role": "assistant", "content": response.content})
    if block is not None:
        retry_content = [{
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"The plan failed schema validation:\n{error}\n\nCall {TOOL_NAME} again with a corrected plan that fixes these errors.",
            "is_error": True,
        }]
    else:
        retry_content = f"You did not call {TOOL_NAME}. Call it now with a valid plan."
    messages.append({"role": "user", "content": retry_content})

    start = time.monotonic()
    retry = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        tools=tools,
        tool_choice=tool_choice,
        messages=messages,
    )
    latency_ms = int((time.monotonic() - start) * 1000)

    retry_block = _extract_tool_use(retry)
    if retry_block is not None:
        try:
            plan = QueryPlan.model_validate(retry_block.input)
            logger.log_interaction(
                request_id, MODEL, system_prompt_hash, question,
                retry.to_dict(), plan, latency_ms, "retry_success",
            )
            return plan
        except ValidationError as exc:
            retry_error = str(exc)
    else:
        retry_error = "model did not return a build_query_plan tool call on retry"

    logger.log_interaction(
        request_id, MODEL, system_prompt_hash, question,
        retry.to_dict(), None, latency_ms, "retry_failed", retry_error,
    )
    raise PlannerError(retry_error)


if __name__ == "__main__":
    import uuid

    questions = [
        "Top 10 vendors paid by Health Care Authority",
        "How much did Molina receive in total?",
        "Which agency spent the most on travel?",
        "What was the largest single payment in the dataset?",
        "What's interesting about Boeing?",
    ]
    for question in questions:
        request_id = uuid.uuid4().hex[:12]
        print("=" * 80)
        print(f"Q: {question}   (request_id={request_id})")
        try:
            plan = plan_query(question, request_id)
            print(plan.model_dump_json(indent=2))
        except PlannerError as exc:
            print(f"PlannerError: {exc}")
