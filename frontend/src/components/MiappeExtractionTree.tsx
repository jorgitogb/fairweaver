import { useState } from "react";
import {
  Sprout,
  MapPin,
  Leaf,
  Globe2,
  FlaskConical,
  Users,
  FileText,
  ChevronRight,
  ChevronDown,
} from "lucide-react";

interface GraphEntity {
  "@id": string;
  "@type": string | string[];
  additionalType?: string;
  name?: string;
  value?: string;
  propertyID?: string;
  additionalProperty?: { "@id": string }[];
  [key: string]: unknown;
}

interface ExtractionField {
  label: string;
  value: string;
  source?: string;
}

interface ExtractionCategory {
  label: string;
  icon: typeof Sprout;
  color: string;
  fields: ExtractionField[];
}

interface Props {
  preview: Record<string, unknown>;
}

const MIAPPE_LABELS: Record<string, string> = {
  "http://purl.obolibrary.org/obo/MIAPPE_0040": "Biological Material ID",
  "http://purl.obolibrary.org/obo/MIAPPE_0041": "Organism",
  "http://purl.obolibrary.org/obo/MIAPPE_0042": "Genus",
  "http://purl.obolibrary.org/obo/MIAPPE_0043": "Species",
  "http://purl.obolibrary.org/obo/MIAPPE_0044": "Infraspecific Name",
  "http://purl.obolibrary.org/obo/MIAPPE_0045": "Organism Latitude",
  "http://purl.obolibrary.org/obo/MIAPPE_0046": "Organism Longitude",
  "http://purl.obolibrary.org/obo/MIAPPE_0047": "Organism Altitude",
  "http://purl.obolibrary.org/obo/MIAPPE_0050": "Material Source ID",
  "http://purl.obolibrary.org/obo/MIAPPE_0051": "Material Source DOI",
  "http://purl.obolibrary.org/obo/MIAPPE_0052": "Source Latitude",
  "http://purl.obolibrary.org/obo/MIAPPE_0053": "Source Longitude",
  "http://purl.obolibrary.org/obo/MIAPPE_0054": "Source Altitude",
  "http://purl.obolibrary.org/obo/MIAPPE_0070": "Observation Unit ID",
  "http://purl.obolibrary.org/obo/MIAPPE_0071": "Observation Unit Type",
  "http://purl.obolibrary.org/obo/MIAPPE_0077": "Development Stage",
  "http://purl.obolibrary.org/obo/MIAPPE_0083": "Variable ID",
  "http://purl.obolibrary.org/obo/MIAPPE_0084": "Variable Name",
  "http://purl.obolibrary.org/obo/MIAPPE_0086": "Trait",
  "http://purl.obolibrary.org/obo/AGRO_00000574": "Field Latitude",
  "http://purl.obolibrary.org/obo/AGRO_00000575": "Field Longitude",
  "http://purl.obolibrary.org/obo/AGRO_00000612": "Field Altitude",
};

function resolveRef(
  ref: string | { "@id": string } | undefined,
  entityMap: Map<string, GraphEntity>
): GraphEntity | undefined {
  if (!ref) return undefined;
  const id = typeof ref === "string" ? ref : ref["@id"];
  return entityMap.get(id);
}

function formatValue(val: unknown): string {
  if (val === undefined || val === null) return "";
  if (typeof val === "string" || typeof val === "number") return String(val);
  if (Array.isArray(val)) return val.map(formatValue).join(", ");
  if (typeof val === "object" && "@id" in (val as Record<string, unknown>)) {
    return (val as { "@id": string })["@id"];
  }
  return JSON.stringify(val);
}

function getLabel(cv: GraphEntity): string {
  if (cv.propertyID && MIAPPE_LABELS[cv.propertyID]) {
    return MIAPPE_LABELS[cv.propertyID];
  }
  return cv.name || "Unknown";
}

function extractMiappeData(graph: GraphEntity[]): ExtractionCategory[] {
  if (!graph || graph.length === 0) return [];

  const entityMap = new Map<string, GraphEntity>();
  for (const e of graph) {
    if (e["@id"]) entityMap.set(e["@id"], e);
  }

  const taxonomy: ExtractionField[] = [];
  const geolocation: ExtractionField[] = [];
  const germplasm: ExtractionField[] = [];
  const originCountry: ExtractionField[] = [];
  const parameters: ExtractionField[] = [];
  const investigation: ExtractionField[] = [];
  const contacts: ExtractionField[] = [];
  const publications: ExtractionField[] = [];

  for (const entity of graph) {
    const type = entity.additionalType || entity["@type"];
    if (type !== "Source") continue;

    const rawProps = entity.additionalProperty;
    const propRefs = Array.isArray(rawProps) ? rawProps : rawProps ? [rawProps] : [];
    const props = propRefs
      .map((ref) => resolveRef(ref, entityMap))
      .filter(Boolean) as GraphEntity[];

    for (const cv of props) {
      const label = getLabel(cv);
      const val = cv.value || "";
      const pid = cv.propertyID || "";

      if (pid.includes("MIAPPE_004") || pid.includes("MIAPPE_005")) {
        if (pid.includes("MIAPPE_0042") || pid.includes("MIAPPE_0043") || pid.includes("MIAPPE_0044")) {
          taxonomy.push({ label, value: formatValue(val), source: entity.name });
        } else if (
          pid.includes("MIAPPE_0045") ||
          pid.includes("MIAPPE_0046") ||
          pid.includes("MIAPPE_0047") ||
          pid.includes("MIAPPE_0052") ||
          pid.includes("MIAPPE_0053") ||
          pid.includes("MIAPPE_0054")
        ) {
          geolocation.push({ label, value: formatValue(val), source: entity.name });
        } else if (pid.includes("MIAPPE_0040") || pid.includes("MIAPPE_0050") || pid.includes("MIAPPE_0051")) {
          germplasm.push({ label, value: formatValue(val), source: entity.name });
        } else {
          taxonomy.push({ label, value: formatValue(val), source: entity.name });
        }
      } else if (pid.includes("AGRO_0000057") || pid.includes("AGRO_00000612")) {
        geolocation.push({ label, value: formatValue(val), source: entity.name });
      } else if (label === "Origin Country") {
        originCountry.push({ label, value: formatValue(val), source: entity.name });
      } else {
        parameters.push({ label, value: formatValue(val), source: entity.name });
      }
    }
  }

  for (const entity of graph) {
    const type = entity.additionalType || entity["@type"];
    if (type === "Investigation") {
      if (entity.name) investigation.push({ label: "Title", value: formatValue(entity.name) });
      if (entity.description) investigation.push({ label: "Description", value: formatValue(entity.description) });
      if (entity.identifier) investigation.push({ label: "Identifier", value: formatValue(entity.identifier) });
      if (entity.license) {
        const lic = resolveRef(entity.license as string | { "@id": string }, entityMap);
        investigation.push({ label: "License", value: lic?.name || formatValue(entity.license) });
      }
      if (entity.datePublished) investigation.push({ label: "Date Published", value: formatValue(entity.datePublished) });

      const creators = entity.creator;
      if (Array.isArray(creators)) {
        for (const c of creators) {
          const person = resolveRef(c, entityMap);
          if (person) {
            const name = [person.givenName, person.familyName].filter(Boolean).join(" ");
            const org = person.affiliation ? resolveRef(person.affiliation as string | { "@id": string }, entityMap) : undefined;
            contacts.push({ label: name || formatValue(c), value: org?.name || "" });
          }
        }
      } else if (creators) {
        const person = resolveRef(creators as string | { "@id": string }, entityMap);
        if (person) {
          const name = [person.givenName, person.familyName].filter(Boolean).join(" ");
          const org = person.affiliation ? resolveRef(person.affiliation as string | { "@id": string }, entityMap) : undefined;
          contacts.push({ label: name || formatValue(creators), value: org?.name || "" });
        }
      }

      const cites = entity.citation;
      if (cites) {
        const refs = Array.isArray(cites) ? cites : [cites];
        for (const ref of refs) {
          const article = resolveRef(ref, entityMap);
          if (article) {
            publications.push({
              label: formatValue(article.headline) || formatValue(article.name) || formatValue(ref),
              value: formatValue(article.identifier),
            });
          }
        }
      }
    }
  }

  const categories: ExtractionCategory[] = [];

  if (taxonomy.length > 0) categories.push({ label: "Taxonomy", icon: Sprout, color: "bg-emerald-100 text-emerald-700", fields: taxonomy });
  if (geolocation.length > 0) categories.push({ label: "Geolocation", icon: MapPin, color: "bg-blue-100 text-blue-700", fields: geolocation });
  if (germplasm.length > 0) categories.push({ label: "Germplasm", icon: Leaf, color: "bg-amber-100 text-amber-700", fields: germplasm });
  if (originCountry.length > 0) categories.push({ label: "Origin Country", icon: Globe2, color: "bg-purple-100 text-purple-700", fields: originCountry });
  if (parameters.length > 0) categories.push({ label: "Parameters", icon: FlaskConical, color: "bg-cyan-100 text-cyan-700", fields: parameters });
  if (contacts.length > 0) categories.push({ label: "Contacts", icon: Users, color: "bg-rose-100 text-rose-700", fields: contacts });
  if (publications.length > 0) categories.push({ label: "Publications", icon: FileText, color: "bg-indigo-100 text-indigo-700", fields: publications });
  if (investigation.length > 0) categories.push({ label: "Investigation", icon: FlaskConical, color: "bg-slate-100 text-slate-700", fields: investigation });

  return categories;
}

function CategorySection({ category }: { category: ExtractionCategory }) {
  const [expanded, setExpanded] = useState(true);
  const Icon = category.icon;

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 py-1 px-1.5 rounded hover:bg-slate-100 w-full text-left"
      >
        {expanded ? (
          <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
        ) : (
          <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
        )}
        <Icon className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        <span className="text-xs font-medium text-slate-700">{category.label}</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ml-1 ${category.color}`}>
          {category.fields.length}
        </span>
      </button>
      {expanded && (
        <div className="ml-6 pl-2 border-l border-slate-200 pb-1">
          {category.fields.map((field, i) => (
            <div key={i} className="flex gap-2 py-0.5 text-[11px]">
              <span className="text-slate-400 font-mono w-40 shrink-0 truncate" title={field.label}>
                {field.label}
              </span>
              <span className="text-slate-600 break-all" title={field.value}>
                {field.value || <span className="text-slate-300 italic">empty</span>}
              </span>
              {field.source && (
                <span className="text-slate-300 ml-auto shrink-0" title={`Source: ${field.source}`}>
                  {field.source}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MiappeExtractionTree({ preview }: Props) {
  const graph = (preview?.["@graph"] || []) as GraphEntity[];
  const categories = extractMiappeData(graph);

  if (categories.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400 text-sm">
        No MIAPPE extraction data found in ARC
      </div>
    );
  }

  const totalFields = categories.reduce((sum, c) => sum + c.fields.length, 0);

  return (
    <div className="text-xs space-y-1 p-2">
      <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-1.5 py-1">
        Extracted {totalFields} fields across {categories.length} categories
      </div>
      {categories.map((cat) => (
        <CategorySection key={cat.label} category={cat} />
      ))}
    </div>
  );
}
