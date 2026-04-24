import { useState } from "react";
import { AlertCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import type { MissingField } from "../api/client";

type Level = MissingField["level"];

interface LevelConfig {
  label: string;
  icon: typeof AlertCircle;
  color: string;
  bg: string;
  badge: string;
}

const LEVEL_CONFIG: Record<Level, LevelConfig> = {
  minimum: {
    label: "Required",
    icon: AlertCircle,
    color: "text-red-600",
    bg: "bg-red-50 border-red-200",
    badge: "bg-red-100 text-red-700",
  },
  recommended: {
    label: "Recommended",
    icon: Info,
    color: "text-amber-600",
    bg: "bg-amber-50 border-amber-200",
    badge: "bg-amber-100 text-amber-700",
  },
  optional: {
    label: "Optional",
    icon: Info,
    color: "text-slate-500",
    bg: "bg-slate-50 border-slate-200",
    badge: "bg-slate-100 text-slate-600",
  },
};

function FieldGroup({
  level,
  fields,
}: {
  level: Level;
  fields: MissingField[];
}) {
  const [open, setOpen] = useState(level === "minimum");
  const config = LEVEL_CONFIG[level];
  const Icon = config.icon;

  if (fields.length === 0) return null;

  return (
    <div className={`rounded-lg border ${config.bg} overflow-hidden`}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5"
      >
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className="text-sm font-medium text-slate-700">
            {config.label}
          </span>
          <span
            className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${config.badge}`}
          >
            {fields.length}
          </span>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>
      {open && (
        <ul className="px-4 pb-3 space-y-1.5">
          {fields.map((f) => (
            <li key={f.field} className="text-sm">
              <span className="font-mono text-slate-800 font-medium">
                {f.field}
              </span>
              {f.description && (
                <span className="text-slate-500 ml-2">— {f.description}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface Props {
  missingFields?: MissingField[];
}

export default function SuggestionPanel({ missingFields = [] }: Props) {
  if (missingFields.length === 0) {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 flex items-center gap-2">
        <span>✅</span>
        All required fields are present for the selected pivot.
      </div>
    );
  }

  const byLevel: Record<Level, MissingField[]> = {
    minimum: missingFields.filter((f) => f.level === "minimum"),
    recommended: missingFields.filter((f) => f.level === "recommended"),
    optional: missingFields.filter((f) => f.level === "optional"),
  };

  return (
    <div>
      <p className="text-sm font-medium text-slate-700 mb-2">
        Missing fields ({missingFields.length})
      </p>
      <div className="space-y-2">
        <FieldGroup level="minimum" fields={byLevel.minimum} />
        <FieldGroup level="recommended" fields={byLevel.recommended} />
        <FieldGroup level="optional" fields={byLevel.optional} />
      </div>
    </div>
  );
}
