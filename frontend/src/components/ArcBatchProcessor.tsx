import { useState } from "react";
import { Upload, FileText, Eye, Download, Loader2, AlertTriangle, CheckCircle, Zip } from "lucide-react";
import { convertBatchToArc } from "../api/client";

interface ArcBatchProcessorProps {
  onBatchComplete?: (filename: string) => void;
}

export default function ArcBatchProcessor({ onBatchComplete }: ArcBatchProcessorProps) {
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [previewResults, setPreviewResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [template, setTemplate] = useState<string>("auto");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith('.zip')) {
        setZipFile(selectedFile);
        setError(null);
        setPreviewResults([]);
      } else {
        setError('Please select a ZIP file');
      }
    }
  };

  const handlePreview = async () => {
    if (!zipFile) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await convertBatchToArc(zipFile, template, true);
      setPreviewResults(Array.isArray(result) ? result : [result]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch preview failed");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExport = async () => {
    if (!zipFile) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const blob = await convertBatchToArc(zipFile, template, false);
      
      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "arc_export_batch.zip";
      a.click();
      URL.revokeObjectURL(url);
      
      if (onBatchComplete) {
        onBatchComplete("arc_export_batch.zip");
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch export failed");
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
        <Zip className="w-12 h-12 text-slate-400 mx-auto mb-4" />
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Upload ZIP File with Multiple Datasets
        </label>
        <input
          type="file"
          accept=".zip"
          onChange={handleFileChange}
          className="hidden"
          id="batch-zip-upload"
        />
        <label
          htmlFor="batch-zip-upload"
          className="cursor-pointer inline-flex items-center justify-center px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          {zipFile ? zipFile.name : "Choose a ZIP file"}
        </label>
        <p className="text-xs text-slate-500 mt-2">
          ZIP file containing multiple Schema.org JSON files
        </p>
      </div>

      {/* Template Selection */}
      {zipFile && (
        <div className="border border-slate-200 rounded-xl p-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Target ARC Template (applied to all files)
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
        </div>
      )}

      {/* Action Buttons */}
      {zipFile && (
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
                Preview All
              </>
            )}
          </button>
          <button
            onClick={handleExport}
            disabled={isProcessing || previewResults.length === 0}
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
                Export All
              </>
            )}
          </button>
        </div>
      )}

      {/* Preview Results */}
      {previewResults.length > 0 && (
        <div className="border border-slate-200 rounded-xl p-4">
          <h3 className="font-semibold text-slate-800 mb-3">Batch Preview</h3>
          <p className="text-sm text-slate-600 mb-4">
            {previewResults.length} files processed
          </p>
          
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {previewResults.map((result, index) => (
              <div key={index} className="border border-slate-100 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700">
                    {result.filename}
                  </span>
                  {result.result.validation.valid ? (
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                  )}
                </div>
                <div className="text-xs">
                  <span className={`font-medium ${result.result.validation.valid ? "text-emerald-600" : "text-amber-600"}`}>
                    {result.result.validation.valid ? "Valid" : "Has issues"}
                  </span>
                  {result.result.validation.errors.length > 0 && (
                    <span className="text-slate-500 ml-2">
                      ({result.result.validation.errors.length} issues)
                    </span>
                  )}
                </div>
              </div>
            ))}
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