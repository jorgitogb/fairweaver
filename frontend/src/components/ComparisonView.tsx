import { useState, useMemo } from "react";
import { Download, ArrowRight, AlertTriangle } from "lucide-react";
import type { FieldRule, MissingField } from "../api/client";

type Tab = "comparison" | "output";

interface Props {
  fieldRules: FieldRule[];
  missingFields: MissingField[];
  output: Record<string, unknown>;
  confidence: number;
  mappingSource?: string;
  model?: string;
}

interface PivotFieldEntry {
  target: string;
  source: string | null;
  required: boolean;
  confidence: number;
  mapped: boolean;
}

export default function ComparisonView({
  fieldRules,
  missingFields,
  output,
  confidence,
  mappingSource,
}: Props) {
  const [tab, setTab] = useState<Tab>("comparison");

  const pivotFields: PivotFieldEntry[] = useMemo(() => {
    const missingTargets = new Set(missingFields.map((f) => f.field));
    return fieldRules.map((r) => ({
      target: r.target,
      source: r.source || null,
      required: r.required,
      confidence: r.confidence,
      mapped: !missingTargets.has(r.target),
    }));
  }, [fieldRules, missingFields]);

  const sourceFields = useMemo(() => {
    return pivotFields
      .filter((f) => f.mapped && f.source)
      .map((f) => f.source!)
      .filter((s, i, arr) => arr.indexOf(s) === i);
  }, [pivotFields]);

  const mappedCount = pivotFields.filter((f) => f.mapped).length;
  const totalCount = pivotFields.length;
  const missingPivotFields = pivotFields.filter((f) => !f.mapped);
  const orphanMissing = useMemo(
    () => missingFields.filter((f) => !pivotFields.some((pf) => pf.target === f.field)),
    [missingFields, pivotFields],
  );

  const downloadOutput = () => {
    const blob = new Blob([JSON.stringify(output, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "fairweaver-output.jsonld";
    a.click();
    URL.revokeObjectURL(url);
  };

   return (
     <div className="rounded-xl border border-slate-200 overflow-hidden w-full">
      {/* Header tabs */}
      <div className="flex items-center justify-between bg-slate-50 border-b border-slate-200 px-4 py-2">
        <div className="flex gap-1">
          {(["comparison", "output"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                tab === t
                  ? "bg-white border border-slate-200 text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t === "comparison" ? "Comparison" : "JSON-LD Output"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
           {mappingSource && (
             <span className="text-xs text-slate-400 font-mono whitespace-nowrap">
               {mappingSource}
             </span>
           )}
          <span
            className={`text-xs font-medium ${
              confidence > 0.7
                ? "text-emerald-600"
                : confidence > 0.4
                  ? "text-amber-600"
                  : "text-red-500"
            }`}
          >
            {Math.round(confidence * 100)}% coverage
          </span>
          <button
            onClick={downloadOutput}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-emerald-600 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Download
          </button>
        </div>
      </div>

      {tab === "output" ? (
         <div className="overflow-x-auto w-full">
           <pre className="text-xs leading-relaxed p-4 overflow-auto max-h-96 bg-slate-900 text-emerald-300 font-mono min-w-fit whitespace-pre">
             {JSON.stringify(output, null, 2)}
           </pre>
         </div>
      ) : (
        <>
           <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-slate-200 min-h-64 w-full">
            {/* ── LEFT: Source Fields ─────────────────────────── */}
            <div className="p-4">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                Input Fields
              </h3>
               {sourceFields.length === 0 ? (
                 <p className="text-xs text-slate-400 italic">No source fields mapped</p>
               ) : (
                 <div className="overflow-x-auto">
                   <ul className="space-y-1.5 min-w-fit">
                     {sourceFields.map((field) => (
                       <li
                         key={field}
                         className="flex items-center gap-2 text-sm font-mono text-slate-700 whitespace-nowrap"
                       >
                         <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                         {field}
                       </li>
                     ))}
                   </ul>
                 </div>
               )}
              <p className="text-xs text-slate-400 mt-3">
                {sourceFields.length} source field{sourceFields.length !== 1 ? "s" : ""} mapped
              </p>
            </div>

            {/* ── RIGHT: Pivot Fields ──────────────────────────── */}
            <div className="p-4">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                Pivot Fields ({mappedCount}/{totalCount})
              </h3>

               {pivotFields.filter((f) => f.mapped).length > 0 && (
                 <div className="overflow-x-auto">
                   <div className="space-y-1 min-w-fit">
                     {pivotFields
                       .filter((f) => f.mapped)
                       .map(renderField)}
                   </div>
                 </div>
               )}

              {pivotFields.length === 0 && (
                <p className="text-xs text-slate-400 italic">No pivot fields defined</p>
              )}
            </div>
          </div>

          {(missingPivotFields.length > 0 || orphanMissing.length > 0) && (
            <div className="border-t border-slate-200 px-4 py-3 bg-slate-50">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3 text-amber-500" />
                Missing Fields ({missingPivotFields.length + orphanMissing.length})
              </h3>
                 <div className="overflow-x-auto">
                   <div className="space-y-1 min-w-fit">
                     {missingPivotFields.map((f) => (
                       <div key={f.target} className="flex items-center gap-1.5 py-0.5 whitespace-nowrap">
                         <span className="w-1.5 h-1.5 rounded-full bg-red-300 shrink-0" />
                         <span className="text-xs font-mono text-slate-500">{f.target}</span>
                         <span className={`text-[10px] font-semibold ${f.required ? "text-red-500" : "text-amber-500"}`}>
                           {f.required ? "required" : "recommended"}
                         </span>
                       </div>
                     ))}
                     {orphanMissing.map((f) => (
                       <div key={f.field} className="flex items-center gap-1.5 py-0.5 whitespace-nowrap">
                         <span className="w-1.5 h-1.5 rounded-full bg-red-300 shrink-0" />
                         <span className="text-xs font-mono text-slate-500">{f.field}</span>
                         <span className="text-[10px] font-semibold text-slate-400">{f.level}</span>
                       </div>
                     ))}
                   </div>
                 </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function renderField(f: PivotFieldEntry) {
  return (
    <div key={f.target} className="flex items-center gap-1.5 py-0.5 whitespace-nowrap">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
      <span className="text-xs font-mono text-slate-700">{f.target}</span>
      {f.source && (
        <span className="text-[10px] text-slate-400 ml-auto flex items-center gap-0.5 whitespace-nowrap">
          <ArrowRight className="w-2.5 h-2.5" />
          {f.source}
        </span>
      )}
    </div>
  );
}
