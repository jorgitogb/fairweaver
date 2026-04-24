import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  convertFile,
  recommendPivot,
  type ConvertResult,
  type PivotRecommendation,
} from "./api/client";
import UploadZone from "./components/UploadZone";
import PivotSelector from "./components/PivotSelector";
import MappingEditor from "./components/MappingEditor";
import SuggestionPanel from "./components/SuggestionPanel";
import { Loader2, Github } from "lucide-react";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [pivotId, setPivotId] = useState<string>("bioschemas_dataset");
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [recommendations, setRecommendations] = useState<PivotRecommendation[]>(
    [],
  );

  const recommendMutation = useMutation({
    mutationFn: (f: File) => recommendPivot(f),
    onSuccess: (data) => {
      setRecommendations(data.recommendations ?? []);
      if (data.recommendations?.length > 0) {
        setPivotId(data.recommendations[0].pivot_id);
      }
    },
  });

  const convertMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("No file selected");
      return convertFile(file, "auto", pivotId);
    },
    onSuccess: (data) => setResult(data),
  });

  const handleFileAccepted = (f: File) => {
    setFile(f);
    setResult(null);
    if (f.name.endsWith(".json")) {
      recommendMutation.mutate(f);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🧬</span>
            <span className="font-bold text-slate-800 tracking-tight">
              FAIRweaver
            </span>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
              v0.1 · pre-hackathon
            </span>
          </div>
          <a
            href="https://github.com/jorgitogb/fairweaver"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors"
          >
            <Github className="w-4 h-4" />
            GitHub
          </a>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Metadata interoperability,{" "}
            <span className="text-emerald-600">FAIR by design</span>
          </h1>
          <p className="text-slate-500 max-w-xl">
            Upload a metadata file, select an interoperability pivot
            (Bioschemas, AgroSchemas, Schema.org…), and get a FAIR-compliant
            JSON-LD output — with AI-assisted field suggestions.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left: upload + pivot */}
          <div className="space-y-6">
            <section>
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                1 · Upload metadata
              </h2>
              <UploadZone onFileAccepted={handleFileAccepted} />
              {file && (
                <p className="mt-2 text-sm text-slate-600 flex items-center gap-1.5">
                  📄 <span className="font-medium">{file.name}</span>
                  <span className="text-slate-400">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </p>
              )}
            </section>

            {file && (
              <section>
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  2 · Choose pivot
                  {recommendMutation.isPending && (
                    <span className="ml-2 text-xs text-amber-500 font-normal normal-case">
                      AI analysing…
                    </span>
                  )}
                </h2>
                <PivotSelector
                  value={pivotId}
                  onChange={setPivotId}
                  recommendations={recommendations}
                />
              </section>
            )}

            {file && (
              <button
                onClick={() => convertMutation.mutate()}
                disabled={convertMutation.isPending}
                className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors"
              >
                {convertMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Converting…
                  </>
                ) : (
                  "Convert to pivot JSON-LD →"
                )}
              </button>
            )}

            {convertMutation.isError && (
              <p className="text-red-500 text-sm">
                ⚠ {(convertMutation.error as Error).message}
              </p>
            )}
          </div>

          {/* Right: output + suggestions */}
          <div className="space-y-6">
            {result ? (
              <>
                <section>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    3 · Output
                  </h2>
                  <MappingEditor
                    output={result.output}
                    missingFields={result.missing_fields}
                    confidence={result.confidence}
                  />
                </section>
                <section>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    4 · FAIR suggestions
                  </h2>
                  <SuggestionPanel missingFields={result.missing_fields} />
                </section>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-300 text-sm text-center p-10 border-2 border-dashed border-slate-200 rounded-xl">
                Output and AI suggestions will appear here after conversion
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="text-center text-xs text-slate-400 py-8">
        FAIRweaver · BioHackathon Germany 2026 · Apache 2.0
      </footer>
    </div>
  );
}
