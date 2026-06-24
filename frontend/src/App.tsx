import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  convertToArc,
  convertFile,
  classifyCompliance,
  type ArcExportResult,
  type ConvertResult,
  type ComplianceResult,
} from "./api/client";
import UploadZone from "./components/UploadZone";
import ArcCrateView from "./components/ArcCrateView";
import ArcScaffoldCreator from "./components/ArcScaffoldCreator";
import ComplianceBadge from "./components/ComplianceBadge";
import { Loader2, Github, Database, ArrowDownUp, AlertTriangle } from "lucide-react";

const PIVOT_OPTIONS = [
  { id: "fairagro_searchhub", label: "FAIRagro Search Hub", category: "FAIRagro" },
  { id: "agrischemas_fieldtrial", label: "AgroSchemas Field Trial", category: "AgroSchemas" },
  { id: "agrischemas_cropvariety", label: "AgroSchemas Crop Variety", category: "AgroSchemas" },
  { id: "bioschemas_dataset", label: "Bioschemas Dataset", category: "Bioschemas" },
];

const isFairagroPivot = (id: string) => id === "fairagro_searchhub";

async function detectSourceFormat(file: File): Promise<string> {
  const text = await file.text();
  try {
    const data = JSON.parse(text);
    const ctx = data["@context"];
    const ctxStr = Array.isArray(ctx) ? ctx.join(" ") : String(ctx ?? "");
    if ("@graph" in data || ctxStr.includes("ro-crate") || ctxStr.includes("ro/crate")) {
      return "ro_crate";
    }
    if (ctxStr.includes("schema.org")) return "schema_org";
  } catch {}
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (ext === "xml") return "datacite_xml";
  if (ext === "csv") return "darwin_core_csv";
  if (ext === "xlsx") return "miappe_xlsx";
  return "isa_json";
}

function getButtonLabel(sourceFormat: string, pivotId: string): string {
  if (sourceFormat === "ro_crate") {
    if (isFairagroPivot(pivotId)) return "Generate FAIRagro JSON-LD →";
    return `Convert to ${PIVOT_OPTIONS.find((p) => p.id === pivotId)?.label ?? pivotId} →`;
  }
  if (isFairagroPivot(pivotId)) return "Convert to ARC RO-Crate →";
  return `Convert to ${PIVOT_OPTIONS.find((p) => p.id === pivotId)?.label ?? pivotId} →`;
}

function getStepLabel(sourceFormat: string, pivotId: string): string {
  if (sourceFormat === "ro_crate") {
    if (isFairagroPivot(pivotId)) return "2 · Generate FAIRagro JSON-LD";
    return `2 · Convert to ${PIVOT_OPTIONS.find((p) => p.id === pivotId)?.label ?? pivotId}`;
  }
  if (isFairagroPivot(pivotId)) return "2 · Convert to ARC RO-Crate";
  return `2 · Convert to ${PIVOT_OPTIONS.find((p) => p.id === pivotId)?.label ?? pivotId}`;
}

function getDescription(sourceFormat: string, pivotId: string): string {
  if (sourceFormat === "ro_crate") {
    if (isFairagroPivot(pivotId)) return "Source is already ARC RO-Crate. Generate FAIRagro-compliant JSON-LD and expose via OAI-PMH.";
    return "Source is already ARC RO-Crate. Transform to target pivot format.";
  }
  if (isFairagroPivot(pivotId)) return "Convert to ARC RO-Crate, generate FAIRagro-compliant JSON-LD, and expose metadata via OAI-PMH.";
  return "Convert input metadata to target pivot format.";
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [sourceFormat, setSourceFormat] = useState<string>("schema_org");
  const [arcResult, setArcResult] = useState<ArcExportResult | null>(null);
  const [pivotResult, setPivotResult] = useState<ConvertResult | null>(null);
  const [complianceResult, setComplianceResult] = useState<ComplianceResult | null>(null);

  const [selectedPivot, setSelectedPivot] = useState("fairagro_searchhub");

  const arcMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("No file selected");
      return convertToArc(file, "auto", selectedPivot, true);
    },
    onSuccess: (data) => { setArcResult(data); setPivotResult(null); },
  });

  const pivotMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("No file selected");
      return convertFile(file, sourceFormat, selectedPivot);
    },
    onSuccess: (data) => { setPivotResult(data); setArcResult(null); },
  });

  const convertMutation = (() => {
    if (isFairagroPivot(selectedPivot)) return arcMutation;
    return pivotMutation;
  })();

  const complianceMutation = useMutation({
    mutationFn: (f: File) => classifyCompliance(f),
    onSuccess: (data) => setComplianceResult(data),
    onError: () => setComplianceResult(null),
  });

  const handleFileAccepted = useCallback(async (f: File) => {
    setFile(f);
    setArcResult(null);
    setPivotResult(null);
    setComplianceResult(null);

    const fmt = await detectSourceFormat(f);
    setSourceFormat(fmt);

    if (fmt !== "ro_crate") {
      complianceMutation.mutate(f);
    }
  }, [complianceMutation]);



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg viewBox="0 0 64 64" className="w-7 h-7" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="hleaf" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2E7D32"/>
                  <stop offset="100%" stopColor="#66BB6A"/>
                </linearGradient>
                <linearGradient id="hdoc" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#f8fafc"/>
                  <stop offset="100%" stopColor="#e2e8f0"/>
                </linearGradient>
              </defs>
              <path d="M16 8 L40 8 L48 16 L48 56 C48 58 46 60 44 60 L20 60 C18 60 16 58 16 56 Z" fill="url(#hdoc)" stroke="#94a3b8" strokeWidth="1.5"/>
              <path d="M40 8 L40 16 L48 16 Z" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" strokeLinejoin="round"/>
              <ellipse cx="32" cy="48" rx="8" ry="2.5" fill="#5D4037"/>
              <path d="M32 48 L32 20" stroke="#2E7D32" strokeWidth="1.8" fill="none" strokeLinecap="round"/>
              <path d="M32 38 C29 35 24 35 22 38 C20 41 24 44 32 41 Z" fill="url(#hleaf)" opacity="0.85"/>
              <path d="M32 33 C35 30 40 30 42 33 C44 36 40 39 32 36 Z" fill="url(#hleaf)" opacity="0.85"/>
              <path d="M32 26 C29 23 24 23 22 26 C20 29 24 32 32 29 Z" fill="url(#hleaf)" opacity="0.85"/>
              <path d="M32 22 C35 19 40 19 42 22 C44 25 40 28 32 25 Z" fill="url(#hleaf)" opacity="0.85"/>
              <path d="M32 16 C31 11 32 8 33 9 C34 10 33 14 32 16 Z" fill="#66BB6A"/>
            </svg>
            <span className="font-bold text-slate-800 tracking-tight">
              FAIRagro-MI
            </span>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
              Demo
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

      <main className="max-w-5xl mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10 space-y-8">
        <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-emerald-200/60">
          <h1 className="text-xl font-semibold text-slate-800 mb-2">
            FAIRagro-MI — metadata inspector (Demo)
          </h1>
          <p className="text-slate-600 max-w-2xl">
            Visual demo tool — manually inspect Schema.org, ARC RO-Crate, and FAIRagro metadata in your browser.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="space-y-6 col-span-1">
            {file ? (
              <>
                <section>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    1 · Upload metadata
                  </h2>
                  <UploadZone onFileAccepted={handleFileAccepted} compact />
                  {file && (
                    <p className="mt-2 text-sm text-slate-600 flex items-center gap-2 flex-wrap">
                      📄 <span className="font-medium truncate max-w-[180px]">{file.name}</span>
                      <span className="text-slate-400">
                        ({(file.size / 1024).toFixed(1)} KB)
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-700">
                        {sourceFormat === "ro_crate" ? "ARC RO-Crate" :
                         sourceFormat === "schema_org" ? "Schema.org" :
                         sourceFormat === "datacite_xml" ? "DataCite XML" :
                         sourceFormat === "darwin_core_csv" ? "Darwin Core CSV" :
                         sourceFormat}
                      </span>
                      {sourceFormat !== "ro_crate" && (
                        <ComplianceBadge
                          result={complianceResult}
                          loading={complianceMutation.isPending}
                        />
                      )}
                    </p>
                  )}
                </section>

                <section>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    {getStepLabel(sourceFormat, selectedPivot)}
                  </h2>
                  <p className="text-xs text-slate-500 mb-3">
                    {getDescription(sourceFormat, selectedPivot)}
                  </p>
                  <div className="mb-3">
                    <label className="text-xs font-medium text-slate-600 flex items-center gap-1 mb-1.5">
                      <ArrowDownUp className="w-3 h-3" /> Target pivot
                    </label>
                    <select
                      value={selectedPivot}
                      onChange={(e) => setSelectedPivot(e.target.value)}
                      className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400"
                    >
                      {PIVOT_OPTIONS.map((opt) => (
                        <option key={opt.id} value={opt.id}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={() => convertMutation.mutate()}
                    disabled={convertMutation.isPending}
                    className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-all shadow-sm hover:shadow-md"
                  >
                    {convertMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Converting…
                      </>
                    ) : (
                      getButtonLabel(sourceFormat, selectedPivot)
                    )}
                  </button>
                </section>

                {convertMutation.isError && (
                  <p className="text-red-500 text-sm flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4 shrink-0" /> {(convertMutation.error as Error).message}
                  </p>
                )}
              </>
            ) : (
              <section>
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  1 · Upload metadata
                </h2>
                <UploadZone onFileAccepted={handleFileAccepted} />
              </section>
            )}
          </div>

          <div className="space-y-6 w-full col-span-2">
            {arcResult ? (
              <>
                <section className="w-full">
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    3 · Results
                  </h2>
                  <ArcCrateView
                    preview={arcResult.preview!}
                    fairagroJsonld={arcResult.fairagro_jsonld!}
                    validation={arcResult.validation}
                    filename={arcResult.filename}
                    oaiIdentifier={arcResult.oai_identifier!}
                  />
                </section>

                {file && arcResult.preview && (
                  <section>
                    <ArcScaffoldCreator
                      rocrateFile={
                        sourceFormat === "ro_crate"
                          ? file
                          : new File(
                              [JSON.stringify(arcResult.preview, null, 2)],
                              "ro-crate.json",
                              { type: "application/json" }
                            )
                      }
                      arcName={arcResult.filename.replace(/_arc-ro-crate\.json$/i, "")}
                    />
                  </section>
                )}
              </>
            ) : pivotResult ? (
              <section className="w-full">
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  3 · Pivot Conversion Result
                </h2>
                <div className="rounded-xl border border-slate-200 overflow-hidden">
                  <div className="flex items-center justify-between bg-slate-50 border-b border-slate-200 px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-700">
                        {PIVOT_OPTIONS.find((p) => p.id === selectedPivot)?.label}
                      </span>
                      <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                        {Math.round((pivotResult.confidence || 0) * 100)}% coverage
                      </span>
                    </div>
                  </div>
                  <pre className="text-xs leading-relaxed p-4 overflow-auto max-h-96 bg-slate-900 text-emerald-300 font-mono whitespace-pre">
                    {JSON.stringify(pivotResult.output, null, 2)}
                  </pre>
                  {pivotResult.missing_fields.length > 0 && (
                    <div className="border-t border-slate-200 bg-slate-50 px-4 py-3">
                      <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                        Missing Fields ({pivotResult.missing_fields.length})
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {pivotResult.missing_fields.map((mf) => (
                          <span
                            key={mf.field}
                            className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                              mf.level === "minimum"
                                ? "bg-red-100 text-red-700"
                                : "bg-amber-100 text-amber-700"
                            }`}
                          >
                            {mf.field}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </section>
            ) : (
              <div className="min-h-[240px] flex items-center justify-center text-slate-400 text-sm text-center p-6 sm:p-10 rounded-xl bg-slate-50/50">
                <div>
                  <Database className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-400">
                    Results will appear here after conversion
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="text-center text-xs text-slate-400 py-8 border-t border-slate-200">
        FAIRagro-MI (metadata inspector, Demo) · BioHackathon Germany 2026
      </footer>
    </div>
  );
}
