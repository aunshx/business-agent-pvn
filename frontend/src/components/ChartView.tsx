import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartSpec } from "../types";

interface Props {
  chartSpec: ChartSpec;
  rows: Record<string, any>[];
  rowCount: number;
  truncated: boolean;
}

function fmtNumber(v: any): string {
  if (typeof v === "number") return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(v);
}

export default function ChartView({ chartSpec, rows, rowCount, truncated }: Props) {
  const { type, x, y } = chartSpec;

  return (
    <div>
      {type === "single_number" && y && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white py-10">
          <div className="text-4xl font-bold text-gray-900">{fmtNumber(rows[0]?.[y])}</div>
          <div className="mt-1 text-sm uppercase tracking-wide text-gray-500">
            {y}
            {x && rows[0]?.[x] ? ` - ${rows[0][x]}` : ""}
          </div>
        </div>
      )}

      {type === "bar" && x && y && (
        <div className="rounded-lg border border-gray-200 bg-white p-3" style={{ height: 380 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ top: 10, right: 20, bottom: 90, left: 70 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x} angle={-30} textAnchor="end" interval={0} height={90} tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={fmtNumber} width={90} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => fmtNumber(v)} />
              <Bar dataKey={y} fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {type === "line" && x && y && (
        <div className="rounded-lg border border-gray-200 bg-white p-3" style={{ height: 380 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 20, left: 70 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x} tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={fmtNumber} width={90} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => fmtNumber(v)} />
              <Line type="monotone" dataKey={y} stroke="#2563eb" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <DataTable rows={rows} rowCount={rowCount} truncated={truncated} />
    </div>
  );
}

function DataTable({ rows, rowCount, truncated }: { rows: Record<string, any>[]; rowCount: number; truncated: boolean }) {
  if (!rows.length) return <p className="mt-4 text-sm text-gray-500">No rows matched.</p>;
  const columns = Object.keys(rows[0]);
  const shown = rows.slice(0, 50);
  return (
    <div className="mt-4">
      <div className="mb-1 text-xs text-gray-500">
        {rowCount.toLocaleString()} row{rowCount === 1 ? "" : "s"}
        {truncated && " (capped at 1,000; showing first 50)"}
        {!truncated && rows.length > 50 && " (showing first 50)"}
      </div>
      <div className="max-h-96 overflow-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 bg-gray-100">
            <tr>
              {columns.map((c) => (
                <th key={c} className="px-3 py-2 text-left font-medium text-gray-700">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                {columns.map((c) => (
                  <td key={c} className="px-3 py-1.5 text-gray-800">
                    {fmtNumber(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
