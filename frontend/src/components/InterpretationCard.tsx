import { useState } from "react";
import { FILTER_COLUMNS, FILTER_OPS, FilterOp, QueryPlan, SchemaSummary } from "../types";

interface Props {
  plan: QueryPlan;
  schema: SchemaSummary | null;
  dirty: boolean;
  onChange: (plan: QueryPlan) => void;
  onRun: () => void;
}

function badgeColor(conf: string) {
  if (conf === "high") return "bg-green-100 text-green-800";
  if (conf === "medium") return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export default function InterpretationCard({ plan, schema, dirty, onChange, onRun }: Props) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [addingFilter, setAddingFilter] = useState(false);

  const columns = schema
    ? Object.keys(schema.columns).filter((c) => FILTER_COLUMNS.includes(c))
    : FILTER_COLUMNS;

  function updateFilter(index: number, patch: Partial<FilterOp>) {
    onChange({ ...plan, filters: plan.filters.map((f, i) => (i === index ? { ...f, ...patch } : f)) });
  }
  function removeFilter(index: number) {
    onChange({ ...plan, filters: plan.filters.filter((_, i) => i !== index) });
  }
  function addFilter(f: FilterOp) {
    onChange({ ...plan, filters: [...plan.filters, f] });
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-lg font-semibold text-gray-900">{plan.interpretation}</h2>
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeColor(plan.confidence)}`}>
          {plan.confidence} confidence
        </span>
      </div>

      {plan.confidence === "low" && (
        <div className="mt-2 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          I wasn't sure about this question. Edit the filters below or rephrase.
        </div>
      )}
      {plan.notes && <p className="mt-2 text-sm text-gray-500">{plan.notes}</p>}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {plan.filters.length === 0 && <span className="text-sm text-gray-400">No filters</span>}
        {plan.filters.map((f, i) => (
          <div key={i} className="flex items-center gap-1 rounded-full border border-gray-300 bg-gray-50 px-2 py-1 text-sm">
            <span className="font-medium text-gray-700">{f.column}</span>
            <span className="text-gray-400">{f.op}</span>
            {editingIndex === i ? (
              <input
                autoFocus
                className="w-44 rounded border border-blue-400 px-1 text-sm"
                defaultValue={String(f.value)}
                onBlur={(e) => {
                  updateFilter(i, { value: e.target.value });
                  setEditingIndex(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    updateFilter(i, { value: (e.target as HTMLInputElement).value });
                    setEditingIndex(null);
                  }
                }}
              />
            ) : (
              <button className="text-blue-700 hover:underline" onClick={() => setEditingIndex(i)}>
                {String(f.value)}
              </button>
            )}
            <button className="ml-1 text-gray-400 hover:text-red-600" onClick={() => removeFilter(i)}>
              ×
            </button>
          </div>
        ))}

        {addingFilter ? (
          <AddFilterRow
            columns={columns}
            onAdd={(f) => {
              addFilter(f);
              setAddingFilter(false);
            }}
            onCancel={() => setAddingFilter(false)}
          />
        ) : (
          <button
            className="rounded-full border border-dashed border-gray-400 px-2 py-1 text-sm text-gray-600 hover:bg-gray-50"
            onClick={() => setAddingFilter(true)}
          >
            + Add filter
          </button>
        )}
      </div>

      {dirty && (
        <button
          onClick={onRun}
          className="mt-3 rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          Run with these changes
        </button>
      )}
    </div>
  );
}

function AddFilterRow({
  columns,
  onAdd,
  onCancel,
}: {
  columns: string[];
  onAdd: (f: FilterOp) => void;
  onCancel: () => void;
}) {
  const [column, setColumn] = useState(columns[0] ?? "Agency");
  const [op, setOp] = useState("equals");
  const [value, setValue] = useState("");
  return (
    <div className="flex items-center gap-1 rounded-full border border-gray-300 bg-white px-2 py-1 text-sm">
      <select value={column} onChange={(e) => setColumn(e.target.value)} className="rounded border border-gray-300 text-sm">
        {columns.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <select value={op} onChange={(e) => setOp(e.target.value)} className="rounded border border-gray-300 text-sm">
        {FILTER_OPS.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
      <input
        className="w-28 rounded border border-gray-300 px-1 text-sm"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="value"
      />
      <button className="text-emerald-700" onClick={() => value.trim() && onAdd({ column, op, value })}>
        ✓
      </button>
      <button className="text-gray-400" onClick={onCancel}>
        ×
      </button>
    </div>
  );
}
