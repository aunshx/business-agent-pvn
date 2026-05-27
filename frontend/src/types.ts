export type Confidence = "high" | "medium" | "low";
export type ChartType = "single_number" | "bar" | "line" | "table";
export type Severity = "info" | "notable" | "high";

export const FILTER_COLUMNS = [
  "Agency",
  "Agy",
  "Vendor",
  "Category",
  "SubCategory",
  "Object",
  "Subobj",
  "FMonth",
  "Amount",
];

export const FILTER_OPS = ["equals", "contains", "in", "gt", "lt", "gte", "lte"];

export interface FilterOp {
  column: string;
  op: string;
  value: any;
}

export interface GroupAgg {
  group_by: string[];
  agg_column: string;
  agg_func: string;
}

export interface QueryPlan {
  interpretation: string;
  filters: FilterOp[];
  grouping: GroupAgg | null;
  sort_by: string | null;
  sort_desc: boolean;
  limit: number | null;
  chart_hint: ChartType;
  confidence: Confidence;
  notes: string | null;
}

export interface ChartSpec {
  type: ChartType;
  x: string | null;
  y: string | null;
  series: string | null;
}

export interface QueryResponse {
  plan: QueryPlan;
  rows: Record<string, any>[];
  row_count: number;
  truncated: boolean;
  chart_spec: ChartSpec;
  request_id: string;
}

export interface Anomaly {
  title: string;
  description: string;
  suggested_question: string;
  severity: Severity;
}

export interface SchemaSummary {
  row_count: number;
  fiscal_year: number;
  biennium: string;
  columns: Record<string, { dtype: string; cardinality: number; values?: string[] }>;
  fmonth_to_calendar: Record<string, string>;
}
