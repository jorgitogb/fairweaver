import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  convertFile,
  getSourceFormats,
  getTemplateFields,
  type ConvertResult,
  type MissingField,
} from "./api/client";
import UploadZone from "./components/UploadZone";
import PivotSelector from "./components/PivotSelector";
import ComparisonView from "./components/ComparisonView";
import MappingEditor from "./components/MappingEditor";
import { Loader2, Upload, Github, Database } from "lucide-react";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [templateId, setTemplateId] = useState<string>("fairagro_searchhub");
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [templateRecommendation, setTemplateRecommendation] = useState<{ recommendedTemplate: string; reason: string } | null>(null);

  const loadSourceFormats = useMutation({
    mutationFn: () => getSourceFormats(),
    onSuccess: () => {},
    onError: (err) => {
      console.error("Failed to load source formats:", err);
    },
  });

  const loadTemplateFields = useMutation({
    mutationFn: (templateId: string) => getTemplateFields(templateId),
    onSuccess: () => {},
    onError: (err) => {
      console.error("Failed to load template fields:", err);
    },
  });

  const convertMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("No file selected");
      return convertFile(file, "auto", templateId);
    },
    onSuccess: (data) => setResult(data),
  });

  const handleFileAccepted = (f: File) => {
    setFile(f);
    setResult(null);
    setTemplateId("fairagro_searchhub");
    setTemplateRecommendation(null);
    
    if (f.name.endsWith(".json")) {
      loadSourceFormats.mutate();
      loadTemplateFields.mutate("fairagro_searchhub");
      
      import("./api/client").then(({ getArcTemplateRecommendation }) => {
        getArcTemplateRecommendation(f)
          .then((rec) => {
            setTemplateRecommendation(rec);
            setTemplateId(rec.recommendedTemplate);
          })
          .catch(() => {});
      });
    }
  };

  const handleTemplateChange = (newTemplateId: string) => {
    setTemplateId(newTemplateId);
    if (newTemplateId !== "auto") {
      loadTemplateFields.mutate(newTemplateId);
    }
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

      <main className="max-w-7xl mx-auto px-6 py-10 space-y-8">
        <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
          <h1 className="text-xl font-semibold text-slate-800 mb-2">
            Schema.org to ARC Playground
          </h1>
          <p className="text-slate-600 max-w-2xl">
            Upload schema.org JSON-LD metadata and convert it to FAIR-compliant ARC RO-Crate format using FAIRagro templates. View field mappings and export ARC JSON.
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
                       2 · Select FAIRagro template
                       {templateRecommendation && (
                         <span className="ml-2 text-xs text-emerald-600 font-normal normal-case">
                           Recommended: {templateRecommendation.recommendedTemplate} ({templateRecommendation.reason})
                         </span>
                       )}
                     </h2>
                     <PivotSelector
                       value={templateId}
                       onChange={handleTemplateChange}
                     />
                  </section>
                )}

                {file && (
                  <button
                    onClick={() => convertMutation.mutate()}
                    disabled={convertMutation.isPending || !templateId}
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
                )}

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
              <section className="w-full">
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  3 · Results
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
            ) : (
              <div className="h-full flex items-center justify-center text-slate-300 text-sm text-center p-10 border-2 border-dashed border-slate-200 rounded-xl">
                <div>
                  <Database className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p>
                    Upload a schema.org JSON file and select a template to see the ARC conversion results
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
