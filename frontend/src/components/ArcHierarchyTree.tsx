import { useState } from "react";
import { ChevronRight, ChevronDown, FileText } from "lucide-react";
import type { GraphEntity } from "./ArcEntityTree";
import { getEntityType, ENTITY_ICONS } from "./ArcEntityTree";

interface Props {
  graph: GraphEntity[];
}

const REF_PROPS = [
  "hasPart",
  "creator",
  "contributor",
  "publisher",
  "affiliation",
  "studyPersonnel",
  "investigationContacts",
  "investigationPublications",
  "author",
  "about",
  "instrument",
  "location",
  "geographicCoverage",
  "soil",
  "process",
  "object",
  "additionalProperty",
  "measurementMethod",
  "measurementTechnique",
  "parameterValue",
  "executesLabProtocol",
  "result",
  "variableMeasured",
];

const REF_LABELS: Record<string, string> = {
  hasPart: "Parts",
  creator: "Creators",
  contributor: "Contributors",
  publisher: "Publisher",
  affiliation: "Affiliation",
  studyPersonnel: "Study Personnel",
  investigationContacts: "Contacts",
  investigationPublications: "Publications",
  author: "Authors",
  about: "About",
  instrument: "Instruments",
  location: "Location",
  geographicCoverage: "Geographic Coverage",
  soil: "Soil",
  process: "Process",
  object: "Object",
  additionalProperty: "Additional Properties",
  measurementMethod: "Measurement Method",
  measurementTechnique: "Measurement Technique",
  parameterValue: "Parameter Values",
  executesLabProtocol: "Protocol",
  result: "Result",
  variableMeasured: "Variable Measured",
};

const REF_SET = new Set(REF_PROPS);

function extractRefIds(val: unknown): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val.flatMap(extractRefIds);
  if (typeof val === "object" && val !== null) {
    const obj = val as Record<string, unknown>;
    if (obj["@id"]) return [String(obj["@id"])];
  }
  return [];
}

function getIcon(type: string) {
  return ENTITY_ICONS[type] || FileText;
}

function findRoot(graph: GraphEntity[], entityMap: Map<string, GraphEntity>): GraphEntity | null {
  const root = entityMap.get("./");
  if (root) return root;
  for (const e of graph) {
    if (getEntityType(e) === "Investigation") return e;
  }
  if (graph.length > 0) return graph[0];
  return null;
}

function HierarchyNode({
  entity,
  entityMap,
  depth,
  visited,
}: {
  entity: GraphEntity;
  entityMap: Map<string, GraphEntity>;
  depth: number;
  visited: Set<string>;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const type = getEntityType(entity);
  const Icon = getIcon(type);
  const name = entity.name || entity["@id"];

  const scalars = Object.entries(entity).filter(([k, v]) => {
    if (REF_SET.has(k)) return false;
    if (k === "@id" || k === "@type" || k === "additionalType" || k === "conformsTo") return false;
    if (v === undefined || v === null) return false;
    if (typeof v === "object" && !Array.isArray(v)) {
      const obj = v as Record<string, unknown>;
      if (Object.keys(obj).length === 0) return false;
      if (obj["@id"]) return false;
    }
    return true;
  });

  const children: { propKey: string; refId: string; refEntity?: GraphEntity }[] = [];
  for (const prop of REF_PROPS) {
    const val = entity[prop];
    if (val === undefined || val === null) continue;
    const refIds = extractRefIds(val);
    for (const refId of refIds) {
      const refEntity = entityMap.get(refId);
      if (refEntity && visited.has(refId)) continue;
      children.push({ propKey: prop, refId, refEntity });
    }
  }

  const groupedChildren = new Map<string, typeof children>();
  for (const child of children) {
    const group = groupedChildren.get(child.propKey) || [];
    group.push(child);
    groupedChildren.set(child.propKey, group);
  }

  const hasContent = scalars.length > 0 || groupedChildren.size > 0;

  return (
    <div style={{ paddingLeft: depth * 16 }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 py-1 px-1.5 rounded hover:bg-slate-100 w-full text-left group"
      >
        {hasContent ? (
          expanded ? (
            <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
          ) : (
            <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
          )
        ) : (
          <span className="w-3 h-3 shrink-0" />
        )}
        <Icon className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        <span className="text-xs font-medium text-slate-700 truncate">{name}</span>
        <span className="text-[10px] text-slate-400 ml-auto">{type}</span>
      </button>

      {expanded && hasContent && (
        <div className="ml-6 pl-2 border-l border-slate-200 pb-1">
          {scalars.map(([key, val]) => (
            <div key={key} className="flex gap-2 py-0.5 text-[11px]">
              <span className="text-slate-400 font-mono w-28 shrink-0 truncate">{key}</span>
              <span className="text-slate-600 break-all">
                {typeof val === "object" ? JSON.stringify(val) : String(val)}
              </span>
            </div>
          ))}

          {Array.from(groupedChildren).map(([propKey, group]) => (
            <div key={propKey} className="mt-1">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-1.5 py-0.5">
                {REF_LABELS[propKey] || propKey} ({group.length})
              </div>
              {group.map((child) => {
                const nextVisited = child.refEntity
                  ? new Set([...visited, child.refId])
                  : visited;
                return child.refEntity ? (
                  <HierarchyNode
                    key={child.refId}
                    entity={child.refEntity}
                    entityMap={entityMap}
                    depth={depth + 1}
                    visited={nextVisited}
                  />
                ) : (
                  <div key={child.refId} style={{ paddingLeft: (depth + 1) * 16 }}>
                    <span className="text-[11px] text-slate-400 italic">{child.refId}</span>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ArcHierarchyTree({ graph }: Props) {
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

  const root = findRoot(graph, entityMap);
  if (!root) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400 text-sm">
        No root entity found
      </div>
    );
  }

  return (
    <div className="text-xs p-2">
      <HierarchyNode
        entity={root}
        entityMap={entityMap}
        depth={0}
        visited={new Set([root["@id"]])}
      />
    </div>
  );
}
