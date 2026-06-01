import { useQuery } from "@tanstack/react-query";
import { fetchPivots, type PivotRecommendation } from "../api/client";
import { Loader2, Layers } from "lucide-react";

interface Props {
  value: string;
  onChange: (id: string) => void;
  recommendations?: PivotRecommendation[];
}

export default function SimplePivotSelector({
  value,
  onChange,
  recommendations = [],
}: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["pivots"],
    queryFn: fetchPivots,
  });

  const pivots = data?.pivots ?? [];

  const getRecommendation = (id: string) =>
    recommendations.find((r) => r.pivot_id === id);

  if (isLoading)
    return (
      <div className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm flex items-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
        <span className="text-slate-400">Loading pivots...</span>
      </div>
    );

  if (error)
    return (
      <div className="w-full border border-red-300 rounded-lg px-3 py-2 text-sm text-red-600">
        Failed to load pivots: {(error as Error).message}
      </div>
    );

  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
        <Layers className="w-4 h-4" />
        Select interoperability pivot
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
      >
        {pivots.map((pivot) => {
          const rec = getRecommendation(pivot.id);
          return (
            <option key={pivot.id} value={pivot.id}>
              {pivot.label}
              {rec && (
                <>
                  {" "}
                  <span className="text-xs text-amber-600 font-semibold">
                    ({rec.coverage_pct}% match)
                  </span>
                </>
              )}
            </option>
          );
        })}
      </select>
    </div>
  );
}