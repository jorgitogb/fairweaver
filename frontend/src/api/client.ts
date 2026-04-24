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
  missing_fields: MissingField[];
  confidence: number;
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
  form.append("source_format", sourceFormat);
  form.append("pivot_id", pivotId);
  return request("/convert", { method: "POST", body: form });
}

export async function convertChain(
  file: File,
  sourceFormat: string,
  pivotId: string,
  targetFormat: string
): Promise<ConvertChainResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("source_format", sourceFormat);
  form.append("pivot_id", pivotId);
  form.append("target_format", targetFormat);
  return request("/convert/chain", { method: "POST", body: form });
}
