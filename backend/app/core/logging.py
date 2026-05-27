import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


class AILogger:
    """POC implementation. Production would write to a persistent store with
    PII detection, retention policy, and replay-for-debugging support. The
    interface here is shaped for that future."""

    def __init__(self, log_file: Path | None = None) -> None:
        self.log_file = log_file or (settings.log_dir / "ai_interactions.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_interaction(
        self,
        request_id: str,
        model: str,
        system_prompt_hash: str,
        user_input: str,
        raw_response: str,
        parsed_plan: Any,
        latency_ms: int,
        validation_status: str,
        error: str | None = None,
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "model": model,
            "system_prompt_hash": system_prompt_hash,
            "user_input": user_input,
            "raw_response": raw_response,
            "parsed_plan": (
                parsed_plan.model_dump()
                if hasattr(parsed_plan, "model_dump")
                else parsed_plan
            ),
            "latency_ms": latency_ms,
            "validation_status": validation_status,
            "error": error,
        }
        with self.log_file.open("a") as f:
            f.write(json.dumps(record, default=str) + "\n")
        summary = (
            f"[AI] {record['timestamp']} req={request_id} model={model} "
            f"status={validation_status} latency={latency_ms}ms"
        )
        if error:
            summary += f" error={error}"
        print(summary)


logger = AILogger()


if __name__ == "__main__":
    logger.log_interaction(
        request_id="test-0001",
        model="claude-sonnet-4-6",
        system_prompt_hash="sha256:abc123",
        user_input="Which agencies spent the most on Personal Service Contracts?",
        raw_response='{"interpretation": "Top agencies by total spend", "chart_hint": "bar"}',
        parsed_plan={
            "interpretation": "Top agencies by total Personal Service Contract spend",
            "filters": [
                {"column": "Category", "op": "equals", "value": "Personal Service Contracts"}
            ],
            "grouping": {"group_by": ["Agency"], "agg_column": "Amount", "agg_func": "sum"},
            "sort_by": "Amount",
            "sort_desc": True,
            "limit": 10,
            "chart_hint": "bar",
            "confidence": "high",
            "notes": None,
        },
        latency_ms=842,
        validation_status="valid",
        error=None,
    )
