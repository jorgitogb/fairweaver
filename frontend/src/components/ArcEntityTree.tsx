import { useState } from "react";
import {
  FlaskConical,
  FileText,
  Users,
  Building2,
  Paperclip,
  Microscope,
  ChevronRight,
  ChevronDown,
  Sprout,
  Bug,
} from "lucide-react";

export interface GraphEntity {
  "@id": string;
  "@type": string | string[];
  additionalType?: string;
  name?: string;
  description?: string;
  [key: string]: unknown;
}

interface Props {
  graph: GraphEntity[];
}

const ENTITY_ICONS: Record<string, typeof FlaskConical> = {
  Investigation: FlaskConical,
  Study: FileText,
  Assay: Microscope,
  Person: Users,
  Organization: Building2,
  File: Paperclip,
};

const DOMAIN_BADGES: Record<string, { icon: typeof Sprout; label: string; color: string }> = {
  crop_species: { icon: Sprout, label: "Crop", color: "bg-emerald-100 text-emerald-700" },
  crop_pest: { icon: Bug, label: "Pest", color: "bg-amber-100 text-amber-700" },
  measurementTechnique: { icon: Microscope, label: "Sensor", color: "bg-blue-100 text-blue-700" },
};

function getEntityType(entity: GraphEntity): string {
  if (entity.additionalType) return entity.additionalType;
  const t = entity["@type"];
  if (Array.isArray(t)) return t[0] || "Unknown";
  return t || "Unknown";
}

function getIcon(type: string) {
  return ENTITY_ICONS[type] || FileText;
}

function DomainBadges({ entity }: { entity: GraphEntity }) {
  const badges = Object.entries(DOMAIN_BADGES)
    .filter(([key]) => entity[key])
    .map(([key, { icon: Icon, label, color }]) => (
      <span key={key} className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium ${color}`}>
        <Icon className="w-2.5 h-2.5" />
        {label}: {String(entity[key])}
      </span>
    ));
  return badges.length > 0 ? <div className="flex flex-wrap gap-1 mt-1">{badges}</div> : null;
}

function EntityNode({ entity, depth }: { entity: GraphEntity; depth: number }) {
  const [expanded, setExpanded] = useState(false);
  const type = getEntityType(entity);
  const Icon = getIcon(type);
  const name = entity.name || entity["@id"];

  const skipKeys = new Set(["@id", "@type", "additionalType", "hasPart", "about", "conformsTo"]);
  const details = Object.entries(entity).filter(
    ([k, v]) => !skipKeys.has(k) && v !== undefined && v !== null && !(typeof v === "object" && !Array.isArray(v) && Object.keys(v as object).length === 0)
  );

  return (
    <div style={{ paddingLeft: depth * 16 }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 py-1 px-1.5 rounded hover:bg-slate-100 w-full text-left group"
      >
        {expanded ? (
          <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
        ) : (
          <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
        )}
        <Icon className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        <span className="text-xs font-medium text-slate-700 truncate">{name}</span>
        <span className="text-[10px] text-slate-400 ml-auto">{type}</span>
      </button>

      {expanded && (
        <div className="ml-6 pl-2 border-l border-slate-200 pb-1">
          <DomainBadges entity={entity} />
          {details.map(([key, val]) => (
            <div key={key} className="flex gap-2 py-0.5 text-[11px]">
              <span className="text-slate-400 font-mono w-28 shrink-0 truncate">{key}</span>
              <span className="text-slate-600 break-all">
                {typeof val === "object" ? JSON.stringify(val) : String(val)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ArcEntityTree({ graph }: Props) {
  if (!graph || graph.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400 text-sm">
        No entities found in ARC graph
      </div>
    );
  }

  const entityMap = new Map<string, GraphEntity>();
  for (const e of graph) {
    if (e["@id"]) entityMap.set(e["@id"], e);
  }

  const investigations = graph.filter((e) => getEntityType(e) === "Investigation");
  const studies = graph.filter((e) => getEntityType(e) === "Study");
  const assays = graph.filter((e) => getEntityType(e) === "Assay");
  const persons = graph.filter((e) => getEntityType(e) === "Person");
  const orgs = graph.filter((e) => getEntityType(e) === "Organization");
  const files = graph.filter((e) => getEntityType(e) === "File");

  const sections = [
    { label: "Investigation", entities: investigations },
    { label: "Study", entities: studies },
    { label: "Assay", entities: assays },
    { label: "Person", entities: persons },
    { label: "Organization", entities: orgs },
    { label: "File", entities: files },
  ].filter((s) => s.entities.length > 0);

  return (
    <div className="text-xs space-y-1 p-2">
      {sections.map((section) => (
        <div key={section.label}>
          <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-1.5 py-1">
            {section.label} ({section.entities.length})
          </div>
          {section.entities.map((entity) => (
            <EntityNode key={entity["@id"]} entity={entity} depth={1} />
          ))}
        </div>
      ))}
    </div>
  );
}
