Video walkthrough outline

A beat sheet, not a script. Rough time targets in parentheses. Talk to the beats in your own words.


Open (about 60 seconds)

State the user and their pain in one breath: a policy analyst at a state agency who needs to answer spending questions, and whose only options today are writing SQL by hand or waiting hours-to-days for an engineer. Make the point that the real cost is the questions that never get asked because the round-trip is too expensive.

Name the goal plainly: collapse that round-trip to seconds, so asking a question is cheap enough to do on impulse. That is the Canva-for-data idea applied to public spending data.

Put the dataset on screen for a second so the domain is concrete: WA State vendor payments, FY2023, just under half a million rows.


Code walk (about 3 to 4 minutes)

Lead with the one idea the whole thing rests on: the model never writes executable code, it fills in a structured QueryPlan. Show app/schemas.py and point at the Literal types on the columns and operations. Say out loud why: free-form SQL means accepting hallucination risk on every query, and a structured plan we validate first means hallucinations get caught at validation, never at runtime.

Show the two walls. First the planner calling Anthropic with tool use and a forced tool_choice, with the input_schema generated from the Pydantic model. Then the Pydantic validation step that re-checks every field in our own process. Make the point that it is two walls on purpose, and that the validation failure path retries once and then refuses rather than guessing.

Connect the structure to the product: because the plan is data and not a string, its filters render as editable chips. Say the line that a SQL string could not be turned into a chip editor without parsing it back into the structure we already have. This is where the safety decision and the differentiating feature turn out to be the same decision.

Briefly show the logging abstraction and the prompt cache: the system prompt is deterministic per schema, cached at roughly 3987 tokens, and we log a short hash of it so the logs group by schema version. Keep this one tight.


Product walk (about 3 to 4 minutes)

Start cold with the anomaly sidebar to show the cold-start path. Click one of the cards, for example the cross-agency vendor or the vendor-concentration one, and show that it populates the query box and runs a real query rather than just displaying a static fact. The point: even the "we tell you what's interesting" path hands control back to the analyst.

Run a clean natural-language query, something like top ten vendors at a named agency. Show the interpretation card with its green confidence badge, the chart, and the data table underneath. This is the happy path: question in, chart out, seconds not days.

Then do the edit-and-rerun, slowly, because this is the differentiator. Take the same query, click the agency filter chip, change the value to a different agency, and click Run with these changes. Show the results actually change. Say that this re-runs through the plan-override path without going back to the model, so the analyst's correction is authoritative.


AI moment (about 1 to 2 minutes)

Tell the Boeing story as a real moment, not a brag. We ran a deliberately vague question, "what's interesting about Boeing," and the first version came back confident with a plausible-looking plan. That was the wrong behavior, because a vague question should not produce a confident answer.

Say the fix explicitly, in these words: confidence reflects how well-specified the question is, not how plausible the guess is. Show that after the reframing, Boeing comes back low confidence with a note listing what it had to guess, and the interpretation card surfaces the "I wasn't sure" prompt.

Close the beat by tying it to trust: the system flagging its own uncertainty, plus the editable card to fix it, is what makes this usable by someone who cannot check the SQL themselves. Optionally mention the Molina substring case as the quieter twin, a confident answer that was still imprecise.


What's next (about 30 to 60 seconds)

Name the two or three deferred items that matter most, briefly and honestly. The data layer moves from in-memory pandas to DuckDB or BigQuery for concurrency and scale, with no change to the plan structure. The planner gets an evaluation suite of question-to-expected-plan pairs so prompt changes cannot silently regress, with the Boeing case as the first entry. Vendor name resolution moves from substring matching to real entity resolution.

End on the through-line: the structured plan is the foundation, and almost everything that scales this to production is swapping an implementation behind that same plan.
