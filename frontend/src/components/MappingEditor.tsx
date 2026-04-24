import { useState } from "react";
import { Download } from "lucide-react";
import type { MissingField } from "../api/client";

type Tab = "output" | "mapping";

interface Props {
  output: Record<string, unknown>;
  missingFields?: MissingField[];
  confidence?: number | null;
}

export default function MappingEditor({ output, confidence }: Props) {
  const [tab, setTab] = useState<Tab>("output");

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
      <div className="flex items-center justify-between bg-slate-50 border-b border-slate-200 px-4 py-2">
        <div className="flex gap-1">
          {(["output", "mapping"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                tab === t
                  ? "bg-white border border-slate-200 text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t === "output" ? "JSON-LD Output" : "Raw Mapping"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {confidence != null && (
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
          )}
          <button
            onClick={downloadOutput}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-emerald-600 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Download
          </button>
        </div>
      </div>

      <pre className="text-xs leading-relaxed p-4 overflow-auto max-h-80 bg-slate-900 text-emerald-300 font-mono">
        {tab === "output"
          ? JSON.stringify(output, null, 2)
          : JSON.stringify(
              { note: "Mapping YAML editor — coming in hackathon week" },
              null,
              2,
            )}
      </pre>
    </div>
  );
}
