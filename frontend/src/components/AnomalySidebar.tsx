import { useEffect, useState } from "react";
import { getAnomalies } from "../api";
import { Anomaly } from "../types";

const dotColor: Record<string, string> = {
  info: "bg-gray-400",
  notable: "bg-amber-500",
  high: "bg-red-500",
};

export default function AnomalySidebar({ onPick }: { onPick: (q: string) => void }) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnomalies()
      .then(setAnomalies)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <aside className="w-80 shrink-0 overflow-auto border-l border-gray-200 bg-gray-50 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-600">
        Anomalies
      </h2>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="space-y-2">
        {anomalies.map((a, i) => (
          <button
            key={i}
            onClick={() => onPick(a.suggested_question)}
            className="block w-full rounded-lg border border-gray-200 bg-white p-3 text-left hover:border-blue-400 hover:shadow-sm"
          >
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 shrink-0 rounded-full ${dotColor[a.severity]}`} />
              <span className="text-sm font-medium text-gray-900">{a.title}</span>
            </div>
            <p className="mt-1 text-xs text-gray-600">{a.description}</p>
          </button>
        ))}
      </div>
    </aside>
  );
}
