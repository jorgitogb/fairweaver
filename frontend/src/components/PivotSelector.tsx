import { useQuery } from "@tanstack/react-query";
import { fetchPivots, type PivotRecommendation } from "../api/client";
import { Layers, Sparkles } from "lucide-react";

const DOMAIN_COLORS: Record<string, string> = {
  agronomy: "bg-green-100 text-green-700",
  plant_phenotyping: "bg-lime-100 text-lime-700",
  biodiversity: "bg-teal-100 text-teal-700",
  genomics: "bg-blue-100 text-blue-700",
  proteomics: "bg-indigo-100 text-indigo-700",
  general: "bg-slate-100 text-slate-600",
  taxonomy: "bg-cyan-100 text-cyan-700",
  soil_science: "bg-amber-100 text-amber-700",
};

interface Props {
  value: string;
  onChange: (id: string) => void;
  recommendations?: PivotRecommendation[];
}

export default function PivotSelector({
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
    return <p className="text-slate-400 text-sm">Loading pivots…</p>;
  if (error)
    return (
      <p className="text-red-500 text-sm">
        Failed to load pivots: {(error as Error).message}
      </p>
    );

  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
        <Layers className="w-4 h-4" />
        Select interoperability pivot
      </label>
      <div className="grid gap-2">
        {pivots.map((pivot) => {
          const rec = getRecommendation(pivot.id);
          const isSelected = value === pivot.id;

          return (
            <button
              key={pivot.id}
              onClick={() => onChange(pivot.id)}
              className={`
                text-left rounded-lg border px-4 py-3 transition-all
                ${
                  isSelected
                    ? "border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500"
                    : "border-slate-200 hover:border-emerald-300 hover:bg-slate-50"
                }
              `}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-800 text-sm">
                    {pivot.label}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {pivot.domains.map((d) => (
                      <span
                        key={d}
                        className={`text-xs px-1.5 py-0.5 rounded ${DOMAIN_COLORS[d] ?? "bg-slate-100 text-slate-500"}`}
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
                {rec && (
                  <div className="flex items-center gap-1 shrink-0">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    <span className="text-xs font-semibold text-amber-600">
                      {rec.coverage_pct}% match
                    </span>
                  </div>
                )}
              </div>
              {(rec?.missing_required?.length ?? 0) > 0 && (
                <p className="text-xs text-red-500 mt-1">
                  Missing required: {rec!.missing_required.join(", ")}
                </p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
