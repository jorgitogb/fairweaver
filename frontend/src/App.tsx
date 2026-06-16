import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  convertToArc,
  classifyCompliance,
  type ArcExportResult,
  type ComplianceResult,
} from "./api/client";
import UploadZone from "./components/UploadZone";
import ArcCrateView from "./components/ArcCrateView";
import ComplianceBadge from "./components/ComplianceBadge";
import { Loader2, Github, Database, Copy, Check, Eye } from "lucide-react";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ArcExportResult | null>(null);
  const [complianceResult, setComplianceResult] = useState<ComplianceResult | null>(null);
  const [oaiCopied, setOaiCopied] = useState(false);

  const convertMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("No file selected");
      return convertToArc(file, "auto", "fairagro_searchhub", true);
    },
    onSuccess: (data) => setResult(data),
  });

  const complianceMutation = useMutation({
    mutationFn: (f: File) => classifyCompliance(f),
    onSuccess: (data) => setComplianceResult(data),
    onError: () => setComplianceResult(null),
  });

  const handleFileAccepted = (f: File) => {
    setFile(f);
    setResult(null);
    setComplianceResult(null);

    complianceMutation.mutate(f);
  };

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
            Schema.org to FAIRagro ARC RO-Crate
          </h1>
          <p className="text-slate-600 max-w-2xl">
            Upload schema.org JSON-LD metadata and convert it to ARC RO-Crate format.
            Generate FAIRagro-compliant JSON-LD for the Search Hub and expose metadata via OAI-PMH.
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
                      <ComplianceBadge
                        result={complianceResult}
                        loading={complianceMutation.isPending}
                      />
                    </p>
                  )}
                </section>

                <section>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    2 · Convert to ARC RO-Crate
                  </h2>
                  <p className="text-xs text-slate-500 mb-3">
                    Uses the FAIRagro template to produce ARC RO-Crate, FAIRagro-compliant JSON-LD, and OAI-PMH endpoint.
                  </p>
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
                      "Convert to ARC RO-Crate →"
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
            {result ? (
              <>
                <section className="w-full">
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    3 · Results
                  </h2>
                  <ArcCrateView
                    preview={result.preview!}
                    fairagroJsonld={result.fairagro_jsonld!}
                    validation={result.validation}
                    filename={result.filename}
                    oaiIdentifier={result.oai_identifier!}
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
            ) : (
              <div className="h-full flex items-center justify-center text-slate-300 text-sm text-center p-10 border-2 border-dashed border-slate-200 rounded-xl">
                <div>
                  <Database className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p>
                    Upload a schema.org JSON file to see the ARC RO-Crate conversion results,
                    FAIRagro-compliant JSON-LD, and OAI-PMH access.
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
