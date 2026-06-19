import { useState, useEffect, useCallback } from "react";
import { Download, CheckCircle, AlertTriangle, XCircle, Copy, Check, Eye, Maximize2, X } from "lucide-react";
import type { ArcValidationResult } from "../api/client";
import ArcEntityTree from "./ArcEntityTree";
import type { GraphEntity } from "./ArcEntityTree";
import MiappeExtractionTree from "./MiappeExtractionTree";
import ArcHierarchyTree from "./ArcHierarchyTree";
import JsonHighlight from "./JsonHighlight";

type Tab = "arc" | "fairagro" | "validation" | "entities" | "hierarchy" | "miappe";

interface Props {
  preview: Record<string, unknown>;
  fairagroJsonld: Record<string, unknown>;
  validation: ArcValidationResult;
  filename: string;
  oaiIdentifier: string;
}

export default function ArcCrateView({
  preview,
  fairagroJsonld,
  validation,
  filename,
  oaiIdentifier,
}: Props) {
  const [tab, setTab] = useState<Tab>("arc");
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") setExpanded(false);
  }, []);

  useEffect(() => {
    if (expanded) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [expanded, handleEscape]);

  const oaiBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000/oai-pmh`;
  const oaiGetRecord = `${oaiBaseUrl}?verb=GetRecord&identifier=${encodeURIComponent(oaiIdentifier)}&metadataPrefix=fairagro_arc`;
  const oaiListRecords = `${oaiBaseUrl}?verb=ListRecords&metadataPrefix=fairagro_arc`;

  const downloadJson = (data: Record<string, unknown>, name: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-slate-200 overflow-hidden w-full">
      {/* Header */}
      <div className="flex items-center justify-between bg-slate-50 border-b border-slate-200 px-4 py-2">
        <span className="text-sm font-medium text-slate-700 truncate">{filename}</span>
        {validation.valid ? (
          <span className="flex items-center gap-1 text-xs text-emerald-600">
            <CheckCircle className="w-3.5 h-3.5" /> Valid
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-amber-600">
            <AlertTriangle className="w-3.5 h-3.5" /> {validation.errors.length} issues
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {(["arc", "fairagro", "validation", "entities", "hierarchy", "miappe"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors border-b-2 whitespace-nowrap ${
              tab === t
                ? "border-emerald-500 text-emerald-700 bg-emerald-50/50"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t === "arc" && "ARC"}
            {t === "fairagro" && "JSON-LD"}
            {t === "validation" && "Validation"}
            {t === "entities" && "Entities"}
            {t === "hierarchy" && "Hierarchy"}
            {t === "miappe" && "MIAPPE"}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="relative">
        {tab === "validation" ? (
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {validation.valid && (
              <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 rounded-lg p-3">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">ARC is valid</span>
              </div>
            )}
            {validation.errors.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <XCircle className="w-3 h-3" /> Errors
                </h4>
                <ul className="space-y-1">
                  {validation.errors.map((err, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-xs text-red-600">
                      <span>•</span>
                      <span>{err}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {validation.warnings.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Warnings
                </h4>
                <ul className="space-y-1">
                  {validation.warnings.map((w, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-xs text-amber-600">
                      <span>•</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-[10px] text-slate-400">
              Template: {validation.template_id} v{validation.template_version}
            </p>
          </div>
        ) : tab === "entities" ? (
          <div className="max-h-96 overflow-y-auto">
            <ArcEntityTree graph={((preview as Record<string, unknown>)?.["@graph"] || []) as GraphEntity[]} />
          </div>
        ) : tab === "hierarchy" ? (
          <div className="max-h-96 overflow-y-auto">
            <ArcHierarchyTree graph={((preview as Record<string, unknown>)?.["@graph"] || []) as GraphEntity[]} />
          </div>
        ) : tab === "miappe" ? (
          <div className="max-h-96 overflow-y-auto">
            <MiappeExtractionTree preview={preview} />
          </div>
        ) : (
          <pre className="text-xs leading-relaxed p-4 overflow-auto max-h-96 bg-slate-900 font-mono whitespace-pre">
            <JsonHighlight data={tab === "arc" ? preview : fairagroJsonld} />
          </pre>
        )}

        {/* Download buttons overlay */}
        <div className="absolute top-2 right-2 flex gap-1.5">
          <button
            onClick={() => setExpanded(true)}
            className="flex items-center gap-1 bg-white/90 hover:bg-white text-slate-700 text-xs px-2 py-1 rounded border border-slate-200 shadow-sm transition-colors"
            title="Expand view"
          >
            <Maximize2 className="w-3 h-3" /> Expand
          </button>
          {tab === "arc" && (
            <button
              onClick={() => downloadJson(preview, filename)}
              className="flex items-center gap-1 bg-white/90 hover:bg-white text-slate-700 text-xs px-2 py-1 rounded border border-slate-200 shadow-sm transition-colors"
            >
              <Download className="w-3 h-3" /> ARC
            </button>
          )}
          {tab === "fairagro" && (
            <button
              onClick={() => downloadJson(fairagroJsonld, "fairagro-searchhub-export.json")}
              className="flex items-center gap-1 bg-white/90 hover:bg-white text-slate-700 text-xs px-2 py-1 rounded border border-slate-200 shadow-sm transition-colors"
            >
              <Download className="w-3 h-3" /> JSON-LD
            </button>
          )}
        </div>
      </div>

      {/* OAI-PMH info */}
      <div className="border-t border-slate-200 bg-slate-50 px-4 py-3 space-y-1.5">
        <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1">
          <Eye className="w-3 h-3" /> OAI-PMH Harvest Endpoint
        </h4>
        <div className="flex items-center gap-2">
          <code className="text-xs bg-white border border-slate-200 rounded px-2 py-1 text-slate-600 truncate flex-1">
            {oaiGetRecord}
          </code>
          <button
            onClick={() => copyToClipboard(oaiGetRecord)}
            className="shrink-0 flex items-center gap-1 text-xs text-slate-500 hover:text-emerald-600 transition-colors"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          </button>
        </div>
        <p className="text-[10px] text-slate-400">
          Use <code className="text-[10px] bg-slate-100 px-1 rounded">ListRecords</code> to harvest all records:{' '}
          <button
            onClick={() => navigator.clipboard.writeText(oaiListRecords)}
            className="text-emerald-600 hover:text-emerald-700 underline"
          >
            copy URL
          </button>
        </p>
      </div>

      {/* Expanded modal */}
      {expanded && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2 bg-slate-50">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-700">{filename}</span>
              <span className="text-xs text-slate-400">—</span>
              <span className="text-xs font-medium text-slate-500">
                {tab === "arc" && "ARC"}
                {tab === "fairagro" && "JSON-LD"}
                {tab === "validation" && "Validation"}
                {tab === "entities" && "Entities"}
                {tab === "hierarchy" && "Hierarchy"}
                {tab === "miappe" && "MIAPPE"}
              </span>
            </div>
            <button
              onClick={() => setExpanded(false)}
              className="p-1.5 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className={`flex-1 overflow-auto ${tab === "arc" || tab === "fairagro" ? "bg-slate-900" : ""}`}>
            {tab === "validation" ? (
              <div className="p-4 space-y-3">
                {validation.valid && (
                  <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 rounded-lg p-3">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">ARC is valid</span>
                  </div>
                )}
                {validation.errors.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Errors
                    </h4>
                    <ul className="space-y-1">
                      {validation.errors.map((err, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-red-600">
                          <span>•</span>
                          <span>{err}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {validation.warnings.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Warnings
                    </h4>
                    <ul className="space-y-1">
                      {validation.warnings.map((w, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-amber-600">
                          <span>•</span>
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="text-[10px] text-slate-400">
                  Template: {validation.template_id} v{validation.template_version}
                </p>
              </div>
            ) : tab === "entities" ? (
              <ArcEntityTree graph={((preview as Record<string, unknown>)?.["@graph"] || []) as GraphEntity[]} />
            ) : tab === "hierarchy" ? (
              <ArcHierarchyTree graph={((preview as Record<string, unknown>)?.["@graph"] || []) as GraphEntity[]} />
            ) : tab === "miappe" ? (
              <MiappeExtractionTree preview={preview} />
            ) : (
              <pre className="text-xs leading-relaxed p-4 bg-slate-900 font-mono whitespace-pre">
                <JsonHighlight data={tab === "arc" ? preview : fairagroJsonld} />
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
