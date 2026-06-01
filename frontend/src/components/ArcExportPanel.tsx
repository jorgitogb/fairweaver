import { useState } from "react";
import { Upload, FileText, Eye, Download, Loader2, AlertTriangle, CheckCircle } from "lucide-react";
import { convertToArc, getArcTemplateRecommendation } from "../api/client";

interface ArcExportPanelProps {
  onExportComplete?: (filename: string) => void;
}

export default function ArcExportPanel({ onExportComplete }: ArcExportPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [template, setTemplate] = useState<string>("auto");
  const [isProcessing, setIsProcessing] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [recommendedTemplate, setRecommendedTemplate] = useState<{
    template: string;
    reason: string;
  } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setError(null);
      setPreviewData(null);
      
      // Auto-recommend template
      getArcTemplateRecommendation(selectedFile)
        .then((result) => {
          setRecommendedTemplate(result);
          if (template === "auto") {
            setTemplate(result.recommendedTemplate);
          }
        })
        .catch(() => {
          setRecommendedTemplate(null);
        });
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await convertToArc(file, "schema_org", template, true);
      setPreviewData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExport = async () => {
    if (!file) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await convertToArc(file, "schema_org", template, false);
      
      // Create download link
      const blob = new Blob([result.arcContent], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.filename;
      a.click();
      URL.revokeObjectURL(url);
      
      if (onExportComplete) {
        onExportComplete(result.filename);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsProcessing(false);
    }
  };

  const templates = [
    { id: "auto", name: "Auto-select (Recommended)" },
    { id: "fairagro_arc_v2", name: "FAIRagro Standard" },
    { id: "fairagro_plant_phenotyping", name: "Plant Phenotyping" },
    { id: "fairagro_genomics", name: "Genomics" },
    { id: "fairagro_sensor", name: "Sensor/Drone" },
  ];

  return (
    <div className="space-y-6">
      {/* File Upload */}
      <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center">
        <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Upload Schema.org JSON File
        </label>
        <input
          type="file"
          accept=".json"
          onChange={handleFileChange}
          className="hidden"
          id="arc-file-upload"
        />
        <label
          htmlFor="arc-file-upload"
          className="cursor-pointer inline-flex items-center justify-center px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          {file ? file.name : "Choose a file"}
        </label>
        <p className="text-xs text-slate-500 mt-2">
          JSON files with Schema.org format
        </p>
      </div>

      {/* Template Selection */}
      {file && (
        <div className="border border-slate-200 rounded-xl p-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Target ARC Template
          </label>
          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
          >
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          {recommendedTemplate && template === "auto" && (
            <div className="mt-2 p-2 bg-blue-50 rounded-lg text-xs text-blue-700 flex items-start gap-2">
              <span>ℹ️</span>
              <span>
                Recommended: <strong>{recommendedTemplate.template}</strong> ({recommendedTemplate.reason})
              </span>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {file && (
        <div className="flex gap-3">
          <button
            onClick={handlePreview}
            disabled={isProcessing}
            className="flex-1 flex items-center justify-center gap-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-60"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Previewing...
              </>
            ) : (
              <>
                <Eye className="w-4 h-4" />
                Preview ARC
              </>
            )}
          </button>
          <button
            onClick={handleExport}
            disabled={isProcessing || !previewData}
            className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-60"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Export ARC
              </>
            )}
          </button>
        </div>
      )}

      {/* Preview Results */}
      {previewData && (
        <div className="border border-slate-200 rounded-xl p-4">
          <h3 className="font-semibold text-slate-800 mb-3">ARC Preview</h3>
          <div className="flex items-center gap-2 mb-3">
            {previewData.validation.valid ? (
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-amber-500" />
            )}
            <span className={`text-sm font-medium ${previewData.validation.valid ? "text-emerald-700" : "text-amber-700"}`}>
              {previewData.validation.valid ? "Valid ARC" : "Validation Issues"}
            </span>
          </div>
          
          {!previewData.validation.valid && (
            <div className="space-y-2 mb-4">
              <p className="text-sm font-medium text-slate-700">Issues:</p>
              <ul className="space-y-1 text-sm">
                {previewData.validation.errors.map((error: string, i: number) => (
                  <li key={i} className="flex items-start gap-1.5 text-red-600">
                    <span className="text-xs">•</span>
                    <span>{error}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="bg-slate-50 rounded-lg p-3 text-sm font-mono">
            <pre className="overflow-x-auto max-h-40">
              {JSON.stringify(previewData.preview, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="border border-red-200 bg-red-50 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}
    </div>
  );
}