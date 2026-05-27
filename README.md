Canva for Data

A natural-language query tool for Washington State vendor payments. You ask a question in plain English, get back a chart and a table, and can correct the system's interpretation if it read the question wrong. Built as a take-home POC against the FY2023 WA vendor payments dataset (484,824 rows, one fiscal year).


Running this locally

You need Python 3.11+, Node 18+, an Anthropic API key, and the provided dataset CSV placed at data/Vendor-Payments_2021-23_FY_2023_.csv.

1. Run ./setup.sh - checks your tools, creates the Python virtual environment, and installs the backend and frontend dependencies. It also creates backend/.env from the template.
2. Open backend/.env and paste your key into ANTHROPIC_API_KEY.
3. Run ./run.sh - starts both servers and prints their URLs.
4. Open the frontend at http://localhost:5173. If that port is taken, Vite prints the actual URL it chose; use that one.

Both scripts are idempotent and safe to re-run. Press Ctrl-C in the run.sh terminal to stop both servers.

The backend is a standard FastAPI package under backend/app: api/ holds the router, services/ holds the planner, executor, dataset, and anomaly logic, core/ holds config and logging, and schemas.py is the Pydantic contract. Configuration is centralized in core/config.py via pydantic-settings, which reads backend/.env. Dev scripts live in backend/scripts.


The problem and the direction we chose

We built for a policy analyst at a state agency or research organization: someone who needs to answer questions about public spending, usually because a stakeholder above them asked one.

Their workflow today is slow either way. With SQL access they write a query, fight the column names, and get an answer in maybe twenty minutes. Without it, the more common case, they file a request and wait for a data engineer. The round-trip on a single question is hours to days, and the real cost is the questions that never get asked: the analyst self-censors down to the few worth the wait. The goal is to collapse that to seconds, so asking is cheap enough to do on impulse.

We passed on two alternatives. Anomaly surfacing alone is a journalist's tool, great when you don't know what you're looking for, but the analyst arrives with a specific question a self-volunteering tool can't answer. A dashboard solves visualization but not the question problem: someone has to define it in advance, and the first unanticipated question sends the analyst back to waiting for an engineer. Natural-language query is the only direction that puts the analyst in the driver's seat for novel questions, which is the actual blocker. The anomaly sidebar stays, but as a cold-start helper: each anomaly is clickable into a real query, so it hands control back rather than keeping it.


Architecture and tech choices

The center of the design is that the language model never writes executable code. It fills in a structured object.

The obvious approach is to have the model emit SQL or pandas and run it. We didn't, because that accepts hallucination risk on every query: the model can invent a column or misname an aggregation, and you find out at runtime with a wrong number on the screen. Instead the planner asks the model to fill a constrained JSON object, the QueryPlan: filters, an optional grouping and aggregation, a sort, a limit, and a chart hint. We validate it before anything executes, so a hallucinated column or unsupported operation is rejected at validation and never reaches the user as a fabricated result.

The constraint is enforced twice. First at the API level: the plan is produced through Anthropic tool use with an input_schema generated from the Pydantic model, and tool_choice forces that shape. Then in Python: every column, operation, aggregation, chart type, and confidence level is a Literal on the Pydantic models, so anything outside the allowed set fails in our own process regardless of what the API returned. The API schema is a strong constraint; the Pydantic layer is the one we fully control.

That decision is also what made the editable interpretation feature, the real differentiator, possible. Because the plan is structured data, we render its parts as controls: filters become chips you can edit or remove, plus an add-filter control backed by the schema. You cannot do that with a SQL string without parsing it back into the structure we already have. The structured format gives us the trust layer and the editing UI for free.

The data flow is linear: question to planner (Anthropic tool use) to a candidate QueryPlan, validated through Pydantic (one retry feeding the error back, then raise rather than guess), to the executor (plain pandas: filter, group and aggregate, sort, limit, cap large results), to a ChartSpec derived from the result shape (single number, bar, line, or table; the model's hint only breaks ties). The response carries the plan, the rows, the chart spec, and a request id.

Two details pay off in production thinking. The system prompt is built fresh each call from the data layer, so it always reflects the current schema, the agency names, and the biennium-month-to-calendar mapping the model needs for a phrase like "April 2023." It is deterministic given the schema, so we cache it: roughly 3987 tokens written once and read from cache on every later request, which is most of the input cost. We also log a short hash of the prompt per interaction, so the logs group by schema version.

Deferred, honestly: the dataset is FY2023 only despite the biennium file name, and the code never pretends otherwise (a union across more DataFrames would not touch the planner or executor). Logging writes JSONL locally through an interface shaped for a real sink, which in production is BigQuery or Datadog with PII scrubbing and retention. Vendor matching is substring-based, fast but imprecise (the Molina case below), where production would do entity resolution against a canonical-name table. Auth, persistence, history, and sharing are not built; the app is single-session and in-memory. Forced tool_choice rules out extended thinking, so we chose structured-output guarantees over reasoning depth. And the in-memory DataFrame will not survive concurrent load; production would back the same plan structure with DuckDB or BigQuery.


What would change in production

The plan structure and the validation layer stay; most of the rest moves.

The biggest change is the data layer. In-memory pandas is right for a 113MB file and one user, and wrong for anything larger or shared. The executor would target a columnar store, DuckDB on a single machine or BigQuery in the cloud, and because the QueryPlan is already structured, the plan-to-SQL translation is mechanical and the planner and frontend do not change.

The logging interface stays as it is; only the sink moves to a persistent store with PII scrubbing and a retention policy. The planner gets an evaluation suite of question-to-expected-plan pairs that runs on every prompt change, so tuning one case cannot silently regress another (the Boeing case below would be the first entry), plus a per-user rate limiter and a cost meter. The frontend gets authentication, persisted query history, shareable links, and typeahead on filter values pulled from the schema endpoint, which we stubbed with a plain input.


AI usage log

The full log is in ai_log.md. Three moments stand out because they show the collaboration doing something other than clean execution.

The Boeing case is the one we lean on. Running the planner's five-question harness, the deliberately vague "What's interesting about Boeing?" came back high confidence with a plausible plan, which is wrong in a way that matters: a vague question should not produce a confident answer, because confidence is what tells the analyst whether to trust the result or edit it. The fix was in the definition of confidence itself. We rewrote the prompt so that confidence reflects how well-specified the question is, not how plausible the guess is, and the rerun returned Boeing at low confidence with a note listing what it had to guess. That reframing is the difference between a demo that looks smart and a tool an analyst can rely on, and you only find it by running the system against a question built to break it.

The second is a quieter version of the same lesson, in the executor. Asked how much the dataset paid Molina, the planner produced a confident-looking plan that matched the vendor name as a substring; the executor ran it faithfully, but the substring "MOLINA" also caught surnames like MOLINARO and KOCHHAR, MOLINA. We chose to keep the executor faithful rather than have it quietly second-guess the plan, because the plan is the contract and the place to fix a bad interpretation is the editable card, not a hidden cleanup step in execution. Boeing shows the system flagging its own uncertainty; Molina shows a confident answer that is still imprecise. Together they are why the card exists.

The third is an engineering catch, in the data layer. The task was a one-line whitespace strip on the string columns. The straightforward version worked, but verification caught that the installed pandas 3 types text as a new string dtype, and that selecting object columns only is deprecated and slated for removal in pandas 4. Left alone it would have silently stopped stripping on a future upgrade, letting dirty data through the one module whose job is to be the clean source of truth. Naming both dtypes explicitly keeps the cleaning working across versions, the difference between code that works today and code that will not surprise someone in a year.
