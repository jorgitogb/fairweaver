import { useState, useMemo } from "react";
import { Download, ChevronDown, ChevronUp, ArrowRight } from "lucide-react";
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
  const [showMissingRequired, setShowMissingRequired] = useState(true);
  const [showMissingRecommended, setShowMissingRecommended] = useState(false);

  const missingRequired = missingFields.filter((f) => f.level === "minimum");
  const missingRecommended = missingFields.filter((f) => f.level === "recommended");

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
    return fieldRules
      .filter((r) => r.source)
      .map((r) => r.source)
      .filter((s, i, arr) => arr.indexOf(s) === i);
  }, [fieldRules]);

  const mappedCount = pivotFields.filter((f) => f.mapped).length;
  const totalCount = pivotFields.length;

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
    <div className="rounded-xl border border-slate-200 overflow-hidden">
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
            <span className="text-xs text-slate-400 font-mono">
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
        <pre className="text-xs leading-relaxed p-4 overflow-auto max-h-96 bg-slate-900 text-emerald-300 font-mono">
          {JSON.stringify(output, null, 2)}
        </pre>
      ) : (
        <div className="grid grid-cols-2 divide-x divide-slate-200 min-h-64">
          {/* ── LEFT: Source Fields ─────────────────────────── */}
          <div className="p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Input Fields
            </h3>
            {sourceFields.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No source fields mapped</p>
            ) : (
              <ul className="space-y-1.5">
                {sourceFields.map((field) => (
                  <li
                    key={field}
                    className="flex items-center gap-2 text-sm font-mono text-slate-700"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                    {field}
                  </li>
                ))}
              </ul>
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

            {/* Required fields */}
            <div className="space-y-1">
              {missingRequired.length > 0 && (
                <button
                  onClick={() => setShowMissingRequired(!showMissingRequired)}
                  className="flex items-center gap-1 text-xs font-semibold text-red-600 mb-1"
                >
                  {showMissingRequired ? (
                    <ChevronUp className="w-3 h-3" />
                  ) : (
                    <ChevronDown className="w-3 h-3" />
                  )}
                  REQUIRED — {missingRequired.length} missing
                </button>
              )}
              {pivotFields
                .filter((f) => f.required)
                .map((f) => {
                  if (f.mapped) return renderField(f);
                  if (showMissingRequired) return renderField(f);
                  return null;
                })}
            </div>

            {/* Recommended fields */}
            <div className="mt-3">
              {missingRecommended.length > 0 && (
                <button
                  onClick={() => setShowMissingRecommended(!showMissingRecommended)}
                  className="flex items-center gap-1 text-xs font-semibold text-amber-600 mb-1"
                >
                  {showMissingRecommended ? (
                    <ChevronUp className="w-3 h-3" />
                  ) : (
                    <ChevronDown className="w-3 h-3" />
                  )}
                  RECOMMENDED — {missingRecommended.length} missing
                </button>
              )}
              {pivotFields
                .filter((f) => !f.required)
                .map((f) => {
                  if (f.mapped) return renderField(f);
                  if (showMissingRecommended) return renderField(f);
                  return null;
                })}
            </div>

            {pivotFields.length === 0 && (
              <p className="text-xs text-slate-400 italic">No pivot fields defined</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function renderField(f: PivotFieldEntry) {
  const dot = f.mapped ? "bg-emerald-400" : "bg-red-300";
  const textColor = f.mapped ? "text-slate-700" : "text-slate-400";
  const label = f.mapped ? "" : f.required ? "MISSING" : "missing";
  const labelColor = f.mapped ? "" : f.required ? "text-red-500" : "text-amber-500";

  return (
    <div key={f.target} className="flex items-center gap-1.5 py-0.5">
      <span className={`w-1.5 h-1.5 rounded-full ${dot} shrink-0`} />
      <span className={`text-xs font-mono ${textColor}`}>{f.target}</span>
      {label && (
        <span className={`text-[10px] font-semibold ${labelColor}`}>{label}</span>
      )}
      {f.source && (
        <span className="text-[10px] text-slate-400 ml-auto flex items-center gap-0.5">
          <ArrowRight className="w-2.5 h-2.5" />
          {f.source}
        </span>
      )}
    </div>
  );
}
