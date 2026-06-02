import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  convertFile,
  recommendPivot,
  harvestConvert,
  type ConvertResult,
  type PivotRecommendation,
  type HarvestConvertRecord,
  type HarvestConvertRequest,
} from "./api/client";
import UploadZone from "./components/UploadZone";
import SimplePivotSelector from "./components/SimplePivotSelector";
import ComparisonView from "./components/ComparisonView";
import HarvestZone from "./components/HarvestZone";
import ArcExportPanel from "./components/ArcExportPanel";
import ArcBatchProcessor from "./components/ArcBatchProcessor";
import ArcTemplateSelector from "./components/ArcTemplateSelector";
import { Loader2, Globe, Upload, Github, ChevronDown, ChevronUp, Database, Package } from "lucide-react";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [pivotId, setPivotId] = useState<string>("fairagro_searchhub");
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [recommendations, setRecommendations] = useState<PivotRecommendation[]>(
    [],
  );
  const [mode, setMode] = useState<"upload" | "harvest" | "arc">("upload");
  const [harvestResults, setHarvestResults] = useState<HarvestConvertRecord[] | null>(null);
  const [harvestError, setHarvestError] = useState<string | null>(null);
  const [expandedRecords, setExpandedRecords] = useState<Set<string>>(new Set());
  const [arcBatchFile, setArcBatchFile] = useState<File | null>(null);
  const [arcTemplate, setArcTemplate] = useState<string>("auto");

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

  const harvestMutation = useMutation({
    mutationFn: (req: HarvestConvertRequest) => harvestConvert(req),
    onSuccess: (data) => {
      setHarvestResults(data.records);
      setHarvestError(null);
    },
    onError: (err) => {
      setHarvestError((err as Error).message);
    },
  });

  const handleFileAccepted = (f: File) => {
    setFile(f);
    setResult(null);
    if (f.name.endsWith(".json")) {
      recommendMutation.mutate(f);
    }
  };

  const handleHarvest = (req: HarvestConvertRequest) => {
    setHarvestResults(null);
    setHarvestError(null);
    setResult(null);
    setFile(null);
    setExpandedRecords(new Set());
    harvestMutation.mutate(req);
  };

  const toggleRecord = (id: string) => {
    setExpandedRecords((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleModeSwitch = (newMode: "upload" | "harvest" | "arc") => {
    setMode(newMode);
    setFile(null);
    setResult(null);
    setHarvestResults(null);
    setHarvestError(null);
    setRecommendations([]);
    setArcBatchFile(null);
    setArcTemplate("auto");
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

       <main className="max-w-7xl mx-auto px-6 py-10 space-y-8">
        {/* Mode toggle */}
        <div>
          <div className="flex items-center gap-2 bg-slate-100 rounded-full p-1 w-fit">
            <button
              onClick={() => handleModeSwitch("upload")}
              className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                mode === "upload"
                  ? "bg-emerald-600 text-white"
                  : "text-slate-600 hover:text-slate-800"
              }`}
            >
              <Upload className="w-4 h-4" />
              Upload File
            </button>
            <button
              onClick={() => handleModeSwitch("harvest")}
              className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                mode === "harvest"
                  ? "bg-emerald-600 text-white"
                  : "text-slate-600 hover:text-slate-800"
              }`}
            >
              <Globe className="w-4 h-4" />
              OAI-PMH Harvest
            </button>
            <button
              onClick={() => handleModeSwitch("arc")}
              className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                mode === "arc"
                  ? "bg-emerald-600 text-white"
                  : "text-slate-600 hover:text-slate-800"
              }`}
            >
              <Database className="w-4 h-4" />
              ARC Export
            </button>
          </div>
          <p className="text-slate-500 max-w-xl mt-3">
            {mode === "upload"
              ? "Upload a metadata file, select an interoperability pivot (Bioschemas, AgroSchemas, Schema.org…), and get a FAIR-compliant JSON-LD output — with AI-assisted field suggestions."
              : mode === "harvest"
              ? "Enter an OAI-PMH endpoint URL to harvest metadata records. Each record will be automatically mapped to the selected pivot and displayed below with field coverage, matched fields, and missing fields."
              : "Convert your metadata to FAIR-compliant ARC RO-Crate format with automatic template selection and validation."
            }
          </p>
        </div>

         <div className="grid lg:grid-cols-2 gap-8">
          {/* Left column */}
          <div className="space-y-6">
            {mode === "upload" ? (
              <>
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
                    <SimplePivotSelector
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

                {result && (
                  <div className="flex items-center gap-2 text-xs">
                    {result.mapping_source === "ai" ? (
                      <span className="flex items-center gap-1 bg-violet-100 text-violet-700 px-2 py-1 rounded-full">
                        <span>🤖</span> AI-powered
                        {result.model && <span className="text-violet-500">({result.model})</span>}
                      </span>
                    ) : result.mapping_source === "rules" ? (
                      <span className="flex items-center gap-1 bg-slate-100 text-slate-600 px-2 py-1 rounded-full">
                        <span>📐</span> Rule-based
                      </span>
                    ) : (
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                        Cached
                      </span>
                    )}
                  </div>
                )}

                {convertMutation.isError && (
                  <p className="text-red-500 text-sm">
                    ⚠ {(convertMutation.error as Error).message}
                  </p>
                )}
              </>
            ) : mode === "arc" ? (
              /* ARC Export mode */
              <section>
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  1 · ARC Export Options
                </h2>
                <div className="space-y-6">
                  <div className="border border-slate-200 rounded-xl p-4">
                    <h3 className="font-medium text-slate-800 flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      Single File Export
                    </h3>
                    <p className="text-sm text-slate-600 mt-2">
                      Convert a single metadata file to ARC RO-Crate format.
                    </p>
                    <div className="mt-3">
                      <ArcExportPanel />
                    </div>
                  </div>
                  
                  <div className="border border-slate-200 rounded-xl p-4">
                    <h3 className="font-medium text-slate-800 flex items-center gap-2">
                      <Package className="w-4 h-4" />
                      Batch Processing
                    </h3>
                    <p className="text-sm text-slate-600 mt-2">
                      Process multiple datasets in a ZIP archive.
                    </p>
                    <div className="mt-3">
                      <ArcBatchProcessor />
                    </div>
                  </div>
                </div>
              </section>
            ) : (
              /* Harvest mode */
              <section>
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  1 · Harvest from OAI-PMH
                </h2>
                <HarvestZone
                  onHarvest={handleHarvest}
                  isHarvesting={harvestMutation.isPending}
                  harvestError={harvestError}
                />
              </section>
            )}
          </div>

           {/* Right: output + suggestions */}
           <div className="space-y-6 w-full">
            {mode === "upload" && result ? (
                 <section className="w-full">
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  3 · Output
                </h2>
                <ComparisonView
                  fieldRules={result.field_rules}
                  missingFields={result.missing_fields}
                  output={result.output}
                  confidence={result.confidence}
                  mappingSource={result.mapping_source}
                  model={result.model}
                />
              </section>
            ) : mode === "harvest" && harvestResults && harvestResults.length > 0 ? (
                 <section className="w-full space-y-4">
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  3 · Harvested Records ({harvestResults.length})
                </h2>
                {harvestResults.map((rec) => {
                  const isExpanded = expandedRecords.has(rec.identifier);
                  return (
                    <div key={rec.identifier} className="border border-slate-200 rounded-xl overflow-hidden">
                      <button
                        onClick={() => toggleRecord(rec.identifier)}
                        className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className={`text-xs font-semibold shrink-0 ${
                            rec.confidence != null && rec.confidence > 0.5
                              ? "text-emerald-600"
                              : "text-amber-600"
                          }`}>
                            {rec.confidence != null ? `${Math.round(rec.confidence * 100)}%` : "—"}
                          </span>
                          <span className="text-xs font-mono text-slate-600 truncate">
                            {rec.identifier.replace("oai:www.openagrar.de:", "")}
                          </span>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
                        )}
                      </button>
                      {isExpanded && (
                        <div className="border-t border-slate-200">
                          <ComparisonView
                            fieldRules={rec.field_rules}
                            missingFields={rec.missing_fields}
                            output={rec.output}
                            confidence={rec.confidence ?? 0}
                            mappingSource={rec.mapping_source}
                            model={rec.model}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </section>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-300 text-sm text-center p-10 border-2 border-dashed border-slate-200 rounded-xl">
                {mode === "upload"
                  ? "Output and AI suggestions will appear here after conversion"
                  : mode === "arc"
                  ? "Select an ARC export option and process to see results here"
                  : "Select a harvested record and convert it — the result will appear here"}
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
