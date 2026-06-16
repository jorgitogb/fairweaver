import { useState, useEffect } from "react";
import { Save, Upload, RefreshCw, AlertTriangle } from "lucide-react";

type Tab = "yaml" | "preview";

interface FieldRule {
  source: string | null;
  target: string;
  required: boolean;
  confidence: number;
  transform: string | null;
  note?: string;
}

interface Mapping {
  source_format: string;
  pivot: string;
  version: string;
  author: string;
  field_rules: FieldRule[];
  ai_generated?: boolean;
  model?: string;
}

interface Props {
  output: Record<string, unknown>;
  confidence?: number;
  fieldRules?: FieldRule[];
  onMappingChange?: (mapping: FieldRule[]) => void;
}

export default function MappingEditor({ output: _output, confidence, fieldRules, onMappingChange: _onMappingChange }: Props) {
  const [tab, setTab] = useState<Tab>("yaml");
  const [yamlContent, setYamlContent] = useState<string>("");
  const [isValidYaml, setIsValidYaml] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  useEffect(() => {
    if (fieldRules) {
      const mapping: Mapping = {
        source_format: "schema_org",
        pivot: "fairagro_searchhub",
        version: "1.0.0",
        author: "fairweaver-user",
        field_rules: fieldRules,
        ai_generated: fieldRules.some(rule => rule.note?.includes("AI") || !rule.note),
        model: fieldRules[0]?.note?.includes("AI") ? "meta-llama-3.1-8b-instruct" : undefined,
      };
      setYamlContent(JSON.stringify(mapping, null, 2));
    }
  }, [fieldRules]);

  const validateYaml = (content: string): boolean => {
    try {
      JSON.parse(content);
      return true;
    } catch (e) {
      setError(`Invalid YAML: ${(e as Error).message}`);
      return false;
    }
  };

  const handleYamlChange = (content: string) => {
    setYamlContent(content);
    if (content.trim()) {
      setIsValidYaml(validateYaml(content));
      setError("");
    } else {
      setIsValidYaml(true);
    }
  };

  const loadFromFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        if (content) {
          setYamlContent(content);
          if (content.trim()) {
            validateYaml(content);
          }
        }
      };
      reader.readAsText(file);
    }
  };

  const saveToFile = () => {
    if (!isValidYaml) return;
    
    const blob = new Blob([yamlContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fairweaver-mapping-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setLastSaved(new Date());
  };

  const loadFromFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    loadFromFile(event);
  };

  const resetToDefault = () => {
    if (fieldRules) {
      const defaultMapping: Mapping = {
        source_format: "schema_org",
        pivot: "fairagro_searchhub",
        version: "1.0.0",
        author: "fairweaver-user",
        field_rules: fieldRules,
        ai_generated: false,
      };
      setYamlContent(JSON.stringify(defaultMapping, null, 2));
      setIsValidYaml(true);
      setError("");
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (confidence > 0.5) return "text-amber-600 bg-amber-50 border-amber-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  return (
    <div className="rounded-xl border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between bg-slate-50 border-b border-slate-200 px-4 py-2">
        <div className="flex gap-1">
          {(["yaml", "preview"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${tab === t
                ? "bg-white border border-slate-200 text-slate-800 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t === "yaml" ? "YAML Editor" : "Preview Output"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {confidence !== undefined && (
            <span className={`text-xs font-medium ${confidence > 0.7 ? "text-emerald-600" : confidence > 0.4 ? "text-amber-600" : "text-red-500"}`}>
              {Math.round(confidence * 100)}% confidence
            </span>
          )}
          {lastSaved && (
            <span className="text-xs text-slate-400">
              Last saved: {lastSaved.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <div className="p-4">
        {tab === "yaml" ? (
          <div className="space-y-4">
            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={saveToFile}
                disabled={!isValidYaml}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Save className="w-4 h-4" />
                Save Mapping
              </button>
              <label className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors cursor-pointer">
                <Upload className="w-4 h-4" />
                Load
                <input
                  type="file"
                  accept=".json,.yaml,.yml"
                  onChange={loadFromFileInput}
                  className="hidden"
                />
              </label>
              <button
                onClick={resetToDefault}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Reset to Default
              </button>
            </div>

            {/* YAML editor */}
            <div className="relative">
              <textarea
                value={yamlContent}
                onChange={(e) => handleYamlChange(e.target.value)}
                className={`w-full h-64 p-3 font-mono text-sm border-2 rounded-lg transition-colors ${isValidYaml ? "border-slate-300 focus:border-emerald-400" : "border-red-300 focus:border-red-400"}`}
                placeholder="Enter YAML mapping..."
              />
              {!isValidYaml && (
                <div className="absolute top-2 right-2 flex items-center gap-1.5 text-red-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-xs">Invalid JSON</span>
                </div>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span className="text-sm text-red-700">{error}</span>
              </div>
            )}

            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>{yamlContent.length} characters</span>
              <span className={`px-2 py-1 rounded ${isValidYaml ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                {isValidYaml ? "Valid JSON" : "Invalid JSON"}
              </span>
            </div>
          </div>
        ) : (
          /* Preview */
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Output Preview</h4>
              <pre className="text-xs font-mono text-slate-600 overflow-x-auto max-h-64">
                {JSON.stringify(JSON.parse(yamlContent || "{}"), null, 2)}
              </pre>
            </div>

            {fieldRules && (
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-2">Field Rules Summary</h4>
                <div className="space-y-1">
                  {fieldRules.map((rule, index) => (
                    <div key={index} className="flex items-center justify-between py-1 border-b border-slate-100">
                      <span className="text-xs font-mono text-slate-600">
                        {rule.source ? `${rule.source} → ` : ""}
                        {rule.target}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 text-xs rounded ${getConfidenceColor(rule.confidence)}`}>
                          {Math.round(rule.confidence * 100)}%
                        </span>
                        {rule.required && (
                          <span className="text-xs text-red-500 font-medium">Required</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
