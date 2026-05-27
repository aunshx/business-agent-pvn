import { Anomaly, QueryPlan, QueryResponse, SchemaSummary } from "./types";

const API_BASE = "http://localhost:8000";

export async function postQuery(question: string, planOverride?: QueryPlan): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, plan_override: planOverride ?? null }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Query failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function getAnomalies(): Promise<Anomaly[]> {
  const res = await fetch(`${API_BASE}/anomalies`);
  if (!res.ok) throw new Error(`Anomalies failed (${res.status})`);
  return res.json();
}

export async function getSchema(): Promise<SchemaSummary> {
  const res = await fetch(`${API_BASE}/schema`);
  if (!res.ok) throw new Error(`Schema failed (${res.status})`);
  return res.json();
}
