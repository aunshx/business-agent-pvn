import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic

from app.core.config import settings
from app.services import dataset

MODEL = settings.planner_model


def main() -> None:
    df = dataset.get_dataframe()
    schema = dataset.get_schema_summary()

    print("=== df.head() ===")
    print(df.head())
    print()
    print(f"rows: {len(df):,}   columns: {list(df.columns)}")
    print()

    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY not set - skipping the Anthropic call.")
        print("Add it to backend/.env to test the LLM pipe.")
        return

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "Hello - here's the schema you'll be working with for a WA "
                    "State vendor payments dataset. Confirm you can read it and "
                    "name one question a policy analyst might ask of it.\n\n"
                    + json.dumps(schema, indent=2)
                ),
            }
        ],
    )

    print("=== Anthropic response ===")
    print(resp.content[0].text)


if __name__ == "__main__":
    main()
