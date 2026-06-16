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
import ComplianceBadge from "./components/ComplianceBadge";
import { Loader2, Github, Database, Copy, Check, Eye, ArrowDownUp } from "lucide-react";

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
  const [oaiCopied, setOaiCopied] = useState(false);
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
    if (sourceFormat === "ro_crate") return pivotMutation;
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

    complianceMutation.mutate(f);
  }, [complianceMutation]);

  const oaiBaseUrl = `http://localhost:8000/oai-pmh`;
  const oaiListRecords = `${oaiBaseUrl}?verb=ListRecords&metadataPrefix=fairagro_arc`;

  const copyOaiUrl = async () => {
    await navigator.clipboard.writeText(oaiListRecords);
    setOaiCopied(true);
    setTimeout(() => setOaiCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50">
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
        <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
          <h1 className="text-xl font-semibold text-slate-800 mb-2">
            FAIRweaver — Metadata Interoperability
          </h1>
          <p className="text-slate-600 max-w-2xl">
            Upload metadata in any format (Schema.org, ARC RO-Crate, DataCite, Darwin Core) and convert
            to the target pivot: FAIRagro Search Hub, AgroSchemas, or Bioschemas.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            {file ? (
              <>
                <section>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    1 · Upload metadata
                  </h2>
                  <UploadZone onFileAccepted={handleFileAccepted} />
                  {file && (
                    <p className="mt-2 text-sm text-slate-600 flex items-center gap-2 flex-wrap">
                      📄 <span className="font-medium">{file.name}</span>
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
                      <ComplianceBadge
                        result={complianceResult}
                        loading={complianceMutation.isPending}
                      />
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
                    className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors"
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
                  <p className="text-red-500 text-sm">
                    ⚠ {(convertMutation.error as Error).message}
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

          <div className="space-y-6 w-full">
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

                <section className="border border-slate-200 rounded-xl p-4 bg-white">
                  <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3 flex items-center gap-1">
                    <Eye className="w-3 h-3" /> OAI-PMH Endpoint
                  </h3>
                  <p className="text-xs text-slate-500 mb-2">
                    Harvest all ARC RO-Crate records via OAI-PMH at:
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-600 truncate flex-1 font-mono">
                      {oaiListRecords}
                    </code>
                    <button
                      onClick={copyOaiUrl}
                      className="shrink-0 flex items-center gap-1 text-xs text-slate-500 hover:text-emerald-600 transition-colors"
                    >
                      {oaiCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-2">
                    Base URL: <code className="text-[10px] bg-slate-100 px-1 rounded">http://localhost:8000/oai-pmh</code>
                  </p>
                </section>
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
              <div className="h-full flex items-center justify-center text-slate-300 text-sm text-center p-10 border-2 border-dashed border-slate-200 rounded-xl">
                <div>
                  <Database className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p>
                    Upload a metadata file (Schema.org, ARC RO-Crate, DataCite XML, Darwin Core CSV)
                    to convert it to your target pivot format.
                  </p>
                </div>
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
