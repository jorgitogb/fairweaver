"""
FAIRweaver Mapping Engine
Handles pivot registry, YAML mapping generation, validation, and conversion.
AI suggestions via Ollama (plugged in later during hackathon week).

## YAML Mapping Schema

Mapping files use this structure:

    source_format: isa_json       # Required: source format ID (e.g., isa_json, datacite_xml)
    pivot: agrischemas_fieldtrial # Required: pivot ID from registry
    version: "0.1.0"        # Required: semantic version
    author: fairweaver-community # Optional: author name
    description: "Maps..."      # Optional: description
    field_rules:               # Required: array of field rules
      - source: study.identifier   # Source field path (nullable = computed/derived)
        target: identifier       # Required: target pivot field
        required: true         # Is required by pivot profile
        confidence: 0.95     # 0.0-1.0 mapping confidence
        transform: null       # Optional: transform function name
        note: "..."        # Optional: human-readable note

## Field Rules

- source: Dot-notation path to field in source document (e.g., "study.title", "submissionDate")
  - Use null if field is computed/derived from multiple sources
- target: Target field name from pivot profile
- required: Whether pivot profile marks this as required
- confidence: 0.0 (no match) to 1.0 (exact match)
  - 0.95+: Exact field name match
  - 0.6-0.9: Fuzzy/alias match
  - 0.0-0.5: No direct equivalent exists
- transform: Optional function name (e.g., "date_iso8601", "uppercase")
- note: Optional explanation for mappers

## Validation

Mappings are validated against MAPPING_SCHEMA_REQUIRED_KEYS:
{"source_format", "pivot", "version", "field_rules"}
"""

import yaml
import json
from pathlib import Path
from typing import Any


MAPPING_SCHEMA_REQUIRED_KEYS = {"source_format", "pivot", "version", "field_rules"}


class MappingEngine:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.pivots = self._load_registry()
        self.mappings_dir = registry_path.parent / "mappings"
        self.mappings_dir.mkdir(exist_ok=True)

    # ── Registry ──────────────────────────────────────────────────────────────

    def _load_registry(self) -> dict:
        with open(self.registry_path) as f:
            data = yaml.safe_load(f)
        return data.get("pivots", {})

    def list_pivots(self) -> list:
        return [
            {
                "id": pid,
                "label": meta.get("label", pid),
                "domains": meta.get("domains", []),
                "context_url": meta.get("context_url", ""),
                "required_fields": meta.get("required_fields", []),
                "recommended_fields": meta.get("recommended_fields", []),
            }
            for pid, meta in self.pivots.items()
        ]

    # ── Pivot recommendation ──────────────────────────────────────────────────

    def recommend_pivot(self, data: dict) -> list:
        """Score each pivot by field coverage against the input document."""
        input_keys = set(self._flatten_keys(data))
        recommendations = []

        for pid, meta in self.pivots.items():
            required = set(meta.get("required_fields", []))
            recommended = set(meta.get("recommended_fields", []))
            all_fields = required | recommended

            if not all_fields:
                continue

            matched = input_keys & all_fields
            coverage = round(len(matched) / len(all_fields) * 100, 1)
            missing_required = list(required - input_keys)

            recommendations.append({
                "pivot_id": pid,
                "label": meta.get("label", pid),
                "coverage_pct": coverage,
                "missing_required": missing_required,
            })

        return sorted(recommendations, key=lambda x: x["coverage_pct"], reverse=True)

    # ── Mappings ──────────────────────────────────────────────────────────────

    def list_mappings(self, source_format: str = None, pivot: str = None) -> list:
        results = []
        for f in self.mappings_dir.glob("*.yaml"):
            with open(f) as fh:
                m = yaml.safe_load(fh)
            if source_format and m.get("source_format") != source_format:
                continue
            if pivot and m.get("pivot") != pivot:
                continue
            results.append({
                "filename": f.name,
                "source_format": m.get("source_format"),
                "pivot": m.get("pivot"),
                "version": m.get("version"),
                "author": m.get("author", "community"),
                "field_count": len(m.get("field_rules", [])),
            })
        return results

    def generate_mapping(self, data: dict, pivot_id: str) -> dict:
        """
        Generate a draft YAML mapping from input data to pivot.
        Rule-based for now; AI (Ollama RAG) replaces this during hackathon week.
        """
        pivot_meta = self.pivots.get(pivot_id, {})
        required = pivot_meta.get("required_fields", [])
        recommended = pivot_meta.get("recommended_fields", [])
        input_keys = list(self._flatten_keys(data))

        field_rules = []
        for target_field in required + recommended:
            # Naive match: exact name or common alias
            source_field = self._find_best_match(target_field, input_keys)
            confidence = 0.9 if source_field == target_field else (0.6 if source_field else 0.0)
            field_rules.append({
                "source": source_field,
                "target": target_field,
                "required": target_field in required,
                "confidence": confidence,
                "transform": None,
            })

        mapping = {
            "source_format": "unknown",
            "pivot": pivot_id,
            "version": "0.1.0",
            "author": "fairweaver-ai",
            "field_rules": field_rules,
        }
        return mapping

    def validate_mapping(self, mapping: dict) -> dict:
        errors = []
        for key in MAPPING_SCHEMA_REQUIRED_KEYS:
            if key not in mapping:
                errors.append(f"Missing required key: '{key}'")
        if "field_rules" in mapping:
            for i, rule in enumerate(mapping["field_rules"]):
                if "target" not in rule:
                    errors.append(f"field_rules[{i}] missing 'target'")
        return {"valid": len(errors) == 0, "errors": errors}

    # ── Conversion ────────────────────────────────────────────────────────────

    def convert(self, data: dict, source_format: str, pivot_id: str) -> dict:
        pivot_meta = self.pivots.get(pivot_id, {})
        context_url = pivot_meta.get("context_url", "https://schema.org")
        required_fields = set(pivot_meta.get("required_fields", []))
        recommended_fields = set(pivot_meta.get("recommended_fields", []))

        # Load best available mapping or fall back to generated draft
        mapping = self._load_best_mapping(source_format, pivot_id)
        if not mapping:
            mapping = self.generate_mapping(data, pivot_id)

        json_ld: dict[str, Any] = {"@context": context_url, "@type": "Dataset"}
        applied_targets = set()

        for rule in mapping.get("field_rules", []):
            source = rule.get("source")
            target = rule.get("target")
            if source and target and source in data:
                json_ld[target] = data[source]
                applied_targets.add(target)

        # Detect missing required and recommended fields
        missing_fields = []
        for field in required_fields - applied_targets:
            missing_fields.append({
                "field": field,
                "level": "minimum",
                "description": f"Required by {pivot_id} profile",
            })
        for field in recommended_fields - applied_targets:
            missing_fields.append({
                "field": field,
                "level": "recommended",
                "description": f"Recommended by {pivot_id} profile",
            })

        total = len(required_fields) + len(recommended_fields)
        confidence = round(len(applied_targets) / total, 2) if total else 1.0

        return {
            "json_ld": json_ld,
            "missing_fields": missing_fields,
            "confidence": confidence,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_best_mapping(self, source_format: str, pivot_id: str):
        for f in self.mappings_dir.glob("*.yaml"):
            with open(f) as fh:
                m = yaml.safe_load(fh)
            if m.get("source_format") == source_format and m.get("pivot") == pivot_id:
                return m
        return None

    def _flatten_keys(self, data: dict, prefix: str = "") -> list:
        keys = []
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(self._flatten_keys(v, full_key))
        return keys

    def _find_best_match(self, target: str, candidates: list) -> str | None:
        # Exact match first
        if target in candidates:
            return target
        # Case-insensitive
        target_lower = target.lower().replace("_", "").replace("-", "")
        for c in candidates:
            if c.lower().replace("_", "").replace("-", "") == target_lower:
                return c
        return None