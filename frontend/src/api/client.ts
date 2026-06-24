// ── Types ─────────────────────────────────────────────────────────────────────

export interface PivotProfile {
  id: string;
  label: string;
  domains: string[];
  context_url: string;
  required_fields: string[];
  recommended_fields: string[];
}

export interface PivotRecommendation {
  pivot_id: string;
  label: string;
  coverage_pct: number;
  missing_required: string[];
}

export interface MappingMeta {
  filename: string;
  source_format: string;
  pivot: string;
  version: string;
  author: string;
  field_count: number;
}

export interface FieldRule {
  source: string | null;
  target: string;
  required: boolean;
  confidence: number;
  transform: string | null;
  note?: string;
}

export interface GeneratedMapping {
  source_format: string;
  pivot: string;
  version: string;
  author: string;
  field_rules: FieldRule[];
  ai_generated?: boolean;
  model?: string;
}

export interface MissingField {
  field: string;
  level: "minimum" | "recommended" | "optional";
  description: string;
}

export interface ConvertResult {
  pivot_id: string;
  source_format: string;
  output: Record<string, unknown>;
  field_rules: FieldRule[];
  missing_fields: MissingField[];
  confidence: number;
  mapping_source?: "ai" | "rules" | "cached";
  model?: string;
}

export interface ConvertChainResult {
  source_format: string;
  pivot_id: string;
  target_format: string;
  output: Record<string, unknown>;
  missing_fields: MissingField[];
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

// ── OAI-PMH Harvesting ─────────────────────────────────────────────────────────

export interface HarvestRequest {
  base_url: string;
  metadata_prefix: "oai_dc" | "oai_datacite";
  set?: string;
  from_date?: string;
  until_date?: string;
  max_records?: number;
}

export interface HarvestedRecord {
  identifier: string;
  datestamp: string;
  set_spec: string[];
  metadata: Record<string, string[]>;
  metadata_format: string;
}

export interface HarvestResult {
  records: HarvestedRecord[];
  total: number;
  metadata_format: string;
}

export interface SetInfo {
  spec: string;
  name: string;
}

export interface ListSetsResponse {
  sets: SetInfo[];
}

export interface HarvestConvertRequest {
  base_url: string;
  metadata_prefix?: string;
  set?: string;
  from_date?: string;
  until_date?: string;
  max_records?: number;
  pivot_id?: string;
}

export interface HarvestConvertRecord extends ConvertResult {
  identifier: string;
  datestamp: string;
  set_spec: string[];
}

export interface HarvestConvertResponse {
  records: HarvestConvertRecord[];
  total: number;
}

export async function listSets(baseUrl: string): Promise<ListSetsResponse> {
  return request("/list-sets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_url: baseUrl }),
  });
}

export async function harvestOAIPMH(
  req: HarvestRequest
): Promise<HarvestResult> {
  return request("/harvest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function harvestConvert(
  req: HarvestConvertRequest
): Promise<HarvestConvertResponse> {
  return request("/harvest/convert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

// ── HTTP helper ───────────────────────────────────────────────────────────────

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── Pivots ────────────────────────────────────────────────────────────────────

export async function fetchPivots(): Promise<{ pivots: PivotProfile[] }> {
  return request("/pivots");
}

export async function recommendPivot(
  file: File
): Promise<{ recommendations: PivotRecommendation[] }> {
  const form = new FormData();
  form.append("file", file);
  return request("/pivots/recommend", { method: "POST", body: form });
}

// ── Mappings ──────────────────────────────────────────────────────────────────

export async function fetchMappings(
  sourceFormat?: string,
  pivot?: string
): Promise<{ mappings: MappingMeta[] }> {
  const params = new URLSearchParams();
  if (sourceFormat) params.set("source_format", sourceFormat);
  if (pivot) params.set("pivot", pivot);
  return request(`/mappings?${params.toString()}`);
}

export async function generateMapping(
  file: File,
  pivotId: string
): Promise<{ mapping: GeneratedMapping; pivot_id: string }> {
  const form = new FormData();
  form.append("file", file);
  form.append("pivot_id", pivotId);
  return request("/mappings/generate", { method: "POST", body: form });
}

export async function validateMapping(file: File): Promise<ValidationResult> {
  const form = new FormData();
  form.append("file", file);
  return request("/mappings/validate", { method: "POST", body: form });
}

// ── Conversion ────────────────────────────────────────────────────────────────

export async function convertFile(
  file: File,
  sourceFormat: string,
  pivotId: string
): Promise<ConvertResult> {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams();
  params.set("source_format", sourceFormat);
  params.set("pivot_id", pivotId);
  return request(`/convert?${params.toString()}`, { method: "POST", body: form });
}

export async function convertChain(
  file: File,
  sourceFormat: string,
  pivotId: string,
  targetFormat: string
): Promise<ConvertChainResult> {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams();
  params.set("source_format", sourceFormat);
  params.set("pivot_id", pivotId);
  params.set("target_format", targetFormat);
   return request(`/convert/chain?${params.toString()}`, { method: "POST", body: form });
}

// ── ARC Template API ────────────────────────────────────────────────────────

export interface ArcValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  template_id: string;
  template_version: string;
}

export async function validateArcFairagro(
  file: File
): Promise<ArcValidationResult> {
  const form = new FormData();
  form.append("file", file);
  return request("/arc/validate/fairagro", {
    method: "POST",
    body: form,
  });
}

export interface SourceFormat {
  source_format: string;
  fields: SourceField[];
}

export interface SourceField {
  name: string;
  label: string;
  description: string;
  required: boolean;
  examples?: string[];
}

export async function getSourceFormats(): Promise<SourceFormat> {
  return request("/source-formats/schema-org");
}

export interface TemplateField {
  name: string;
  label: string;
  description: string;
  required: boolean;
  examples?: string[];
  category?: "mandatory" | "recommended";
}

export interface TemplateFieldGroup {
  category: "mandatory" | "recommended";
  fields: TemplateField[];
}

export async function getTemplateFields(templateId: string): Promise<TemplateFieldGroup[]> {
  return request(`/template-fields/${templateId}`);
}

export async function getFairagroArcTemplate(): Promise<{
  template_id: string;
  name: string;
  description: string;
  version: string;
  required_entities: string[];
  required_fields: Record<string, string[]>;
}> {
  return request("/arc/templates/fairagro");
}

export interface ArcExportResult {
  arcContent?: string;
  preview?: Record<string, unknown>;
  fairagro_jsonld?: Record<string, unknown>;
  validation: ArcValidationResult;
  filename: string;
  oai_identifier?: string;
}

export interface ArcBatchPreviewResult {
  filename: string;
  result: ArcExportResult;
}

export interface ArcBatchExportResult {
  filename: string;
  arc_filename: string;
  validation: ArcValidationResult;
}

export async function createArcScaffold(file: File): Promise<Blob> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch("/arc/scaffold", {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "ARC scaffold creation failed" }));
    throw new Error(error.detail || "ARC scaffold creation failed");
  }

  return response.blob();
}

export interface ArcTemplateRecommendation {
  recommendedTemplate: string;
  reason: string;
}

export async function convertToArc(
  file: File,
  sourceFormat: string = "auto",
  pivotId: string = "fairagro_searchhub",
  preview: boolean = false
): Promise<ArcExportResult> {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams();
  params.set("source_format", sourceFormat);
  params.set("pivot_id", pivotId);
  params.set("preview", preview.toString());

  const response = await fetch(`/convert/arc-export?${params.toString()}`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "ARC export failed");
  }

  if (preview) {
    return await response.json();
  }

  const arcContent = await response.text();
  const validation = await validateArcFairagro(new File([arcContent], "temp.json"));

  const contentDisposition = response.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch ? filenameMatch[1] : "arc-ro-crate.json";

  return { arcContent, validation, filename };
}

export async function convertBatchToArc(
  zipFile: File,
  pivotId: string = "fairagro_searchhub",
  preview: boolean = false
): Promise<ArcBatchPreviewResult[] | Blob> {
  const form = new FormData();
  form.append("file", zipFile);
  const params = new URLSearchParams();
  params.set("pivot_id", pivotId);
  params.set("batch", "true");
  params.set("preview", preview.toString());

  const response = await fetch(`/convert/arc-export?${params.toString()}`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Batch ARC export failed");
  }

  if (preview) {
    return await response.json();
  }

  return await response.blob();
}

export async function getArcTemplateRecommendation(
  file: File
): Promise<{ recommendedTemplate: string; reason: string }> {
  // Analyze file content to recommend appropriate template
  const content = await file.text();
  try {
    const data = JSON.parse(content);
    
    // Simple heuristic-based recommendation
    if (data.crop_species || data.organism) {
      return {
        recommendedTemplate: "fairagro_plant_phenotyping",
        reason: "Detected crop/plant-related data"
      };
    }
    
    if (data.sequencing || data.dna || data.rna) {
      return {
        recommendedTemplate: "fairagro_genomics",
        reason: "Detected genomics-related data"
      };
    }
    
    if (data.drone || data.sensor || data.measurementTechnique) {
      return {
        recommendedTemplate: "fairagro_sensor",
        reason: "Detected sensor/measurement data"
      };
    }
    
    return {
      recommendedTemplate: "fairagro_searchhub",
      reason: "General FAIRagro template recommended"
    };
  } catch (e) {
    return {
      recommendedTemplate: "fairagro_searchhub",
      reason: "Could not analyze file content, using default template"
    };
  }
}

// ── Compliance Classification ──────────────────────────────────────────────

export interface ComplianceBreakdown {
  present: string[];
  missing: string[];
  score: number;
}

export interface ComplianceResult {
  level: "basic" | "intermediate" | "full";
  source_format: string;
  breakdown: {
    required: ComplianceBreakdown;
    recommended: ComplianceBreakdown;
    full: ComplianceBreakdown;
  };
  overall_score: number;
}

export async function classifyCompliance(
  file: File
): Promise<ComplianceResult> {
  const form = new FormData();
  form.append("file", file);
  return request("/compliance/classify", {
    method: "POST",
    body: form,
  });
}
