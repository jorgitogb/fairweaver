import { type ComplianceResult } from "../api/client";
import { ShieldCheck, ShieldAlert, Shield, Loader2, AlertTriangle } from "lucide-react";

interface Props {
  result?: ComplianceResult | null;
  loading?: boolean;
  error?: string | null;
}

const LEVEL_STYLE: Record<string, string> = {
  basic: "bg-red-100 text-red-700 border-red-200",
  intermediate: "bg-amber-100 text-amber-700 border-amber-200",
  full: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

const LEVEL_ICON: Record<string, typeof ShieldCheck> = {
  basic: ShieldAlert,
  intermediate: Shield,
  full: ShieldCheck,
};

const LEVEL_LABEL: Record<string, string> = {
  basic: "Basic",
  intermediate: "Intermediate",
  full: "Full",
};

export default function ComplianceBadge({ result, loading, error }: Props) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border bg-slate-100 text-slate-500 border-slate-200">
        <Loader2 className="w-3 h-3 animate-spin" />
        Analyzing…
      </span>
    );
  }

  if (error) {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border bg-red-50 text-red-600 border-red-200"
      >
        <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
        {error}
      </span>
    );
  }

  if (!result) return null;

  const level = result.level;
  const style = LEVEL_STYLE[level] ?? LEVEL_STYLE.basic;
  const Icon = LEVEL_ICON[level] ?? ShieldAlert;
  const label = LEVEL_LABEL[level] ?? "Unknown";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${style}`}
      title={`${result.overall_score}% FAIRagro compliance`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
      <span className="opacity-60 font-normal">
        {result.overall_score}%
      </span>
    </span>
  );
}
