import { useState, useEffect } from "react";
import { Info } from "lucide-react";
import { getArcTemplateRecommendation } from "../api/client";

interface ArcTemplateSelectorProps {
  file: File;
  value: string;
  onChange: (templateId: string) => void;
}

export default function ArcTemplateSelector({ file, value, onChange }: ArcTemplateSelectorProps) {
  const [recommendation, setRecommendation] = useState<{
    template: string;
    reason: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getRecommendation = async () => {
      try {
        setLoading(true);
        const result = await getArcTemplateRecommendation(file);
        setRecommendation({ template: result.recommendedTemplate, reason: result.reason });
        // Auto-select if current value is "auto"
        if (value === "auto") {
          onChange(result.recommendedTemplate);
        }
      } catch (error) {
        setRecommendation(null);
      } finally {
        setLoading(false);
      }
    };

    getRecommendation();
  }, [file]);

  const templates = [
    { id: "auto", name: "Auto-select (Recommended)" },
    { id: "fairagro_arc_v2", name: "FAIRagro Standard" },
    { id: "fairagro_plant_phenotyping", name: "Plant Phenotyping" },
    { id: "fairagro_genomics", name: "Genomics" },
    { id: "fairagro_sensor", name: "Sensor/Drone" },
  ];

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-700">
        ARC Template
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400"
      >
        {templates.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>

      {loading ? (
        <div className="text-xs text-slate-500 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-slate-300 animate-pulse" />
          Analyzing file...
        </div>
      ) : recommendation && value === "auto" ? (
        <div className="p-2 bg-blue-50 rounded-lg text-xs text-blue-700 flex items-start gap-2">
          <Info className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
          <span>
            Auto-selected: <strong>{recommendation.template}</strong> 
            ({recommendation.reason})
          </span>
        </div>
      ) : null}
    </div>
  );
}