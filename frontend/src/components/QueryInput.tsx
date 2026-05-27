const EXAMPLES = [
  "Top 10 vendors at DSHS",
  "Largest single payment",
  "Which agency spent the most on travel",
];

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (q: string) => void;
  loading: boolean;
}

export default function QueryInput({ value, onChange, onSubmit, loading }: Props) {
  return (
    <div className="w-full">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (value.trim()) onSubmit(value.trim());
        }}
        className="flex gap-2"
      >
        <input
          className="flex-1 rounded border border-gray-300 px-4 py-2 text-base focus:border-blue-500 focus:outline-none"
          placeholder="Ask a question about WA State vendor payments..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="rounded bg-blue-600 px-5 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? "Running..." : "Ask"}
        </button>
      </form>
      <div className="mt-2 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => onSubmit(ex)}
            disabled={loading}
            className="rounded-full border border-gray-300 bg-gray-50 px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
