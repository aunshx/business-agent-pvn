import { useEffect, useState } from "react";
import AnomalySidebar from "./components/AnomalySidebar";
import ChartView from "./components/ChartView";
import InterpretationCard from "./components/InterpretationCard";
import QueryInput from "./components/QueryInput";
import { getSchema, postQuery } from "./api";
import { QueryPlan, QueryResponse, SchemaSummary } from "./types";

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [editedPlan, setEditedPlan] = useState<QueryPlan | null>(null);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schema, setSchema] = useState<SchemaSummary | null>(null);

  useEffect(() => {
    getSchema().then(setSchema).catch(() => {});
  }, []);

  async function run(q: string) {
    setQuestion(q);
    setLoading(true);
    setError(null);
    try {
      const res = await postQuery(q);
      setResponse(res);
      setEditedPlan(res.plan);
      setDirty(false);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function runOverride() {
    if (!editedPlan) return;
    setLoading(true);
    setError(null);
    try {
      const res = await postQuery(question, editedPlan);
      setResponse(res);
      setEditedPlan(res.plan);
      setDirty(false);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  function onPlanChange(plan: QueryPlan) {
    setEditedPlan(plan);
    setDirty(true);
  }

  return (
    <div className="flex h-screen flex-col bg-gray-100">
      <header className="border-b border-gray-200 bg-white px-6 py-3">
        <h1 className="text-xl font-bold text-gray-900">Canva for Data</h1>
        <p className="text-sm text-gray-500">
          WA State vendor payments, FY2023 - ask a question, get a chart.
        </p>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-auto p-6">
          <QueryInput value={question} onChange={setQuestion} onSubmit={run} loading={loading} />

          {error && (
            <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          {response && editedPlan && (
            <div className="mt-6 space-y-6">
              <InterpretationCard
                plan={editedPlan}
                schema={schema}
                dirty={dirty}
                onChange={onPlanChange}
                onRun={runOverride}
              />
              <ChartView
                chartSpec={response.chart_spec}
                rows={response.rows}
                rowCount={response.row_count}
                truncated={response.truncated}
              />
            </div>
          )}

          {!response && !loading && (
            <div className="mt-10 text-center text-gray-400">
              Ask a question or click an anomaly to begin.
            </div>
          )}
        </main>

        <AnomalySidebar onPick={run} />
      </div>
    </div>
  );
}
