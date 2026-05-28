# Canva for Data

> Ask a question in plain English, get back a chart and a table, and correct the system's interpretation if it read the question wrong.

A take-home POC: a natural-language query tool for Washington State vendor payments, built against the FY2023 dataset (484,824 rows, one fiscal year).


## Running locally

**Prerequisites:** Python 3.11+, Node 18+, an Anthropic API key, and the provided dataset CSV placed at `data/Vendor-Payments_2021-23_FY_2023_.csv`.

```bash
./setup.sh   # one-time: checks tools, creates the venv, installs deps, writes backend/.env
# then open backend/.env and paste your key into ANTHROPIC_API_KEY
./run.sh     # starts the backend (:8000) and the frontend (:5173)
```

Then open the frontend at http://localhost:5173. If that port is taken, Vite prints the actual URL it chose; use that one. Both scripts are idempotent and safe to re-run, and Ctrl-C in the `run.sh` terminal stops both servers.

**Try asking:**

- "Top 10 vendors paid by Health Care Authority"
- "How much did Molina receive in total?"
- "Which agency spent the most on travel?"
- "What was the largest single payment in the dataset?"
- "What's interesting about Boeing?"

The last one is deliberately vague: it comes back low confidence, which is the cue to edit the interpretation or rephrase. The example pills under the input box and the anomaly cards in the sidebar are other good starting points.

**Project layout:** the backend is a standard FastAPI package under `backend/app`: `api/` holds the router, `services/` holds the planner, executor, dataset, and anomaly logic, `core/` holds config and logging, and `schemas.py` is the Pydantic contract. Configuration is centralized in `core/config.py` via pydantic-settings, which reads `backend/.env`. Dev scripts live in `backend/scripts`.


## The problem and the direction we chose

We built for a policy analyst at a state agency or research organization: someone who answers questions about public spending, usually because a stakeholder above them asked one.

Their workflow today is slow either way. With SQL access they write a query, fight the column names, and answer in maybe twenty minutes; without it, the more common case, they file a request and wait for a data engineer. The round-trip is hours to days, and the real cost is the questions that never get asked: the analyst self-censors down to the few worth the wait. The goal is to collapse that to seconds.

We passed on two alternatives. Anomaly surfacing alone is a journalist's tool, good when you don't know what you're looking for, but the analyst arrives with a specific question it can't answer. A dashboard solves visualization but not the question problem: someone defines it in advance, and the first unanticipated question sends the analyst back to waiting for an engineer. Natural-language query is the only direction that puts the analyst in the driver's seat for novel questions, which is the actual blocker. The anomaly sidebar stays as a cold-start helper: each card is clickable into a real query, so it hands control back rather than keeping it.


## Architecture and tech choices

**The key idea:** the language model never writes executable code. It fills in a structured object that we validate before anything runs.

The obvious approach is to have the model emit SQL or pandas and run it. We didn't, because that accepts hallucination risk on every query: the model can invent a column or misname an aggregation, and you find out at runtime with a wrong number on the screen. Instead the planner has the model fill a constrained JSON object, the `QueryPlan`: filters, an optional grouping and aggregation, a sort, a limit, and a chart hint. We validate it before executing, so a hallucinated column or unsupported operation is rejected at validation and never reaches the user as a fabricated result.

**The constraint is enforced twice.** First at the API level: the plan comes through Anthropic tool use with an `input_schema` generated from the Pydantic model, and `tool_choice` forces that shape. Then in Python: every column, operation, aggregation, chart type, and confidence level is a `Literal` on the models, so anything outside the allowed set fails in our own process regardless of what the API returned. The API schema is a strong constraint; the Pydantic layer is the one we fully control.

That decision also made the editable interpretation feature, the real differentiator, possible. Because the plan is structured data, we render its parts as controls: filters become chips you can edit or remove, with an add-filter control backed by the schema. You can't do that with a SQL string without parsing it back into the structure we already have. The format gives us the trust layer and the editing UI for free.

The data flow is linear: question to planner (Anthropic tool use) to a candidate `QueryPlan`, validated through Pydantic (one retry feeding the error back, then raise rather than guess), to the executor (plain pandas: filter, group and aggregate, sort, limit, cap large results), to a `ChartSpec` derived from the result shape (single number, bar, line, or table; the model's hint only breaks ties). The response carries the plan, rows, chart spec, and a request id.

Two details pay off later. The system prompt is built fresh each call from the data layer, so it always reflects the current schema, agency names, and the biennium-month-to-calendar mapping the model needs for a phrase like "April 2023." It's deterministic given the schema, so we cache it: ~3987 tokens written once and read from cache on every later request, most of the input cost. We also log a short hash of the prompt per interaction, so logs group by schema version.

**Deferred, honestly:** the dataset is FY2023 only despite the biennium file name, and the code never pretends otherwise (a union across more DataFrames wouldn't touch the planner or executor). Logging writes JSONL locally through an interface shaped for a real sink (BigQuery or Datadog with PII scrubbing and retention). Vendor matching is substring-based, fast but imprecise (the Molina case below); production would do entity resolution against a canonical-name table. Auth, persistence, history, and sharing aren't built; the app is single-session and in-memory. Forced `tool_choice` rules out extended thinking, so we chose structured-output guarantees over reasoning depth. And the in-memory DataFrame won't survive concurrent load; production would back the same plan with DuckDB or BigQuery.


## What would change in production

The plan structure and the validation layer stay; most of the rest moves.

The biggest change is the data layer. In-memory pandas is right for a 113MB file and one user, wrong for anything larger or shared. The executor would target a columnar store, DuckDB on a single machine or BigQuery in the cloud, and because the `QueryPlan` is already structured, plan-to-SQL is mechanical and the planner and frontend don't change.

The logging interface stays; only the sink moves to a persistent store with PII scrubbing and retention. The planner gets an evaluation suite of question-to-expected-plan pairs that runs on every prompt change, so tuning one case can't silently regress another (the Boeing case below would be the first entry), plus a per-user rate limiter and cost meter. The frontend gets authentication, persisted query history, shareable links, and typeahead on filter values from the schema endpoint, which we stubbed with a plain input.


## AI usage log

The full log is in `ai_log.md`. Three moments stand out because they show the collaboration doing something other than clean execution.

**Boeing: confidence calibration.** Running the planner's five-question harness, the deliberately vague "What's interesting about Boeing?" came back high confidence with a plausible plan, which is wrong in a way that matters: a vague question shouldn't produce a confident answer, because confidence is what tells the analyst whether to trust the result or edit it. The fix was in the definition of confidence itself. We rewrote the prompt so that confidence reflects how well-specified the question is, not how plausible the guess is, and the rerun returned Boeing at low confidence with a note listing what it had to guess. You only find that by running the system against a question built to break it.

**Molina: a confident answer that's still imprecise.** A quieter version of the same lesson, in the executor. Asked how much the dataset paid Molina, the planner matched the vendor name as a substring; the executor ran it faithfully, but "MOLINA" also caught surnames like MOLINARO and KOCHHAR, MOLINA. We kept the executor faithful rather than have it second-guess the plan, because the plan is the contract and the place to fix a bad interpretation is the editable card, not a hidden cleanup in execution. Boeing shows the system flagging its own uncertainty; Molina shows a confident answer that's still imprecise. Together they're why the card exists.

**pandas 3: an engineering catch.** The task was a one-line whitespace strip on the string columns. The straightforward version worked, but verification caught that the installed pandas 3 types text as a new string dtype, and that selecting object columns only is deprecated and slated for removal in pandas 4. Left alone, the strip would silently stop running on a future upgrade, letting dirty data through the one module whose job is to be the clean source of truth. Naming both dtypes explicitly keeps it working across versions.
