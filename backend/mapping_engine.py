"""
FAIRweaver Mapping Engine
Handles pivot registry, YAML mapping generation, validation, and conversion.
Uses rule-based matching with SAIA AI assistance for intelligent suggestions.
"""

import yaml
import json
from pathlib import Path
from typing import Any

from ai_client import generate_mapping_suggestion, is_available


MAPPING_SCHEMA_REQUIRED_KEYS = {"source_format", "pivot", "version", "field_rules"}


class MappingEngine:
    def __init__(self, registry_path: Path, plugins=None):
        self.registry_path = registry_path
        self.pivots = self._load_registry()
        self.mappings_dir = registry_path.parent / "mappings"
        self.mappings_dir.mkdir(exist_ok=True)
        self._last_mapping_ai = False
        self._last_mapping_model = None
        self.plugins = plugins or {}

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

    def recommend_pivot(self, data: dict, source_format: str = None) -> list:
        """Score each pivot by field coverage against the input document."""
        input_keys = set(self._flatten_keys(data))
        recommendations = []

        for pid, meta in self.pivots.items():
            required = set(meta.get("required_fields", []))
            recommended = set(meta.get("recommended_fields", []))

            # ALSO check blocks structure (for pivots like fairagro_searchhub)
            blocks = meta.get("blocks", {})
            for block_name, block_meta in blocks.items():
                required |= set(block_meta.get("required_fields", []))
                recommended |= set(block_meta.get("recommended_fields", []))

            all_fields = required | recommended

            if not all_fields:
                continue

            # Try to load mapping for this pivot to invert source→target lookup
            source_fields = set()
            if source_format:
                mapping = self._load_best_mapping(source_format, pid)
                if mapping:
                    for rule in mapping.get("field_rules", []):
                        src = rule.get("source")
                        tgt = rule.get("target", "")
                        # Add source field if target is a required/recommended field
                        if src and any(tgt.endswith(f) for f in all_fields):
                            source_fields.add(src)

            # If we have mapping source fields, use those; otherwise use target fields directly
            fields_to_check = source_fields if source_fields else all_fields

            matched = input_keys & fields_to_check
            coverage = round(len(matched) / len(fields_to_check) * 100, 1) if fields_to_check else 0

            # Calculate missing based on source→target mapping
            if source_fields:
                missing_required = [
                    f
                    for f in required
                    if not any(
                        any(
                            r.get("source") == src and r.get("target", "").endswith(f)
                            for r in mapping.get("field_rules", [])
                        )
                        for src in input_keys
                    )
                ]
            else:
                missing_required = list(required - input_keys)

            recommendations.append(
                {
                    "pivot_id": pid,
                    "label": meta.get("label", pid),
                    "coverage_pct": coverage,
                    "missing_required": missing_required,
                }
            )

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
            results.append(
                {
                    "filename": f.name,
                    "source_format": m.get("source_format"),
                    "pivot": m.get("pivot"),
                    "version": m.get("version"),
                    "author": m.get("author", "community"),
                    "field_count": len(m.get("field_rules", [])),
                }
            )
        return results

    def generate_mapping(self, data: dict, pivot_id: str) -> dict:
        """
        Generate a draft YAML mapping from input data to pivot.
        Tries AI first if available, falls back to rule-based matching.
        """
        pivot_meta = self.pivots.get(pivot_id, {})
        required = pivot_meta.get("required_fields", [])
        recommended = pivot_meta.get("recommended_fields", [])
        input_keys = self._flatten_keys(data)

        # Try AI first if available
        if is_available():
            pivot_fields = list(
                zip(required + recommended, [f in required for f in required + recommended])
            )
            ai_result = generate_mapping_suggestion(
                source_fields=input_keys,
                pivot_fields=pivot_fields,
                pivot_id=pivot_id,
            )
            if ai_result:
                try:
                    field_rules = json.loads(ai_result)
                    if field_rules and isinstance(field_rules, list):
                        self._last_mapping_ai = True
                        self._last_mapping_model = os.getenv(  # noqa: F821
                            "OPENAI_MODEL", "meta-llama-3.1-8b-instruct"
                        )
                        return {
                            "source_format": "unknown",
                            "pivot": pivot_id,
                            "version": "0.1.0",
                            "author": "fairweaver-ai",
                            "field_rules": field_rules,
                        }
                except json.JSONDecodeError:
                    pass

        # Fall back to rule-based matching
        self._last_mapping_ai = False
        self._last_mapping_model = None
        field_rules = []
        for target_field in required + recommended:
            source_field = self._find_best_match(target_field, input_keys)
            confidence = 0.9 if source_field == target_field else (0.6 if source_field else 0.0)
            field_rules.append(
                {
                    "source": source_field,
                    "target": target_field,
                    "required": target_field in required,
                    "confidence": confidence,
                    "transform": None,
                }
            )

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

        # Load best available mapping or generate new one
        mapping = self._load_best_mapping(source_format, pivot_id)
        mapping_source = "cached"
        if not mapping:
            mapping = self.generate_mapping(data, pivot_id)
            mapping_source = "ai" if self._last_mapping_ai else "rules"

        # Determine mapping source for response
        if mapping_source == "cached" and mapping:
            mapping_source = "cached"

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
            missing_fields.append(
                {
                    "field": field,
                    "level": "minimum",
                    "description": f"Required by {pivot_id} profile",
                }
            )
        for field in recommended_fields - applied_targets:
            missing_fields.append(
                {
                    "field": field,
                    "level": "recommended",
                    "description": f"Recommended by {pivot_id} profile",
                }
            )

        total = len(required_fields) + len(recommended_fields)
        confidence = round(len(applied_targets) / total, 2) if total else 1.0

        return {
            "json_ld": json_ld,
            "field_rules": mapping.get("field_rules", []),
            "missing_fields": missing_fields,
            "confidence": confidence,
            "mapping_source": mapping_source,
            "model": self._last_mapping_model if mapping_source == "ai" else None,
        }

    def convert_nested(self, data: dict, source_format: str, pivot_id: str) -> dict:
        """Convert using nested block structure."""
        pivot_meta = self.pivots.get(pivot_id, {})
        blocks = pivot_meta.get("blocks", {})

        # Load mapping
        mapping = self._load_best_mapping(source_format, pivot_id)
        mapping_source = "cached"
        if not mapping:
            mapping = self.generate_mapping(data, pivot_id)
            mapping_source = "ai" if self._last_mapping_ai else "rules"

        mapping_source = "cached" if mapping_source == "cached" and mapping else mapping_source

        # Group field_rules by block
        rules_by_block = {}
        for rule in mapping.get("field_rules", []):
            block = rule.get("block", "default")
            if block not in rules_by_block:
                rules_by_block[block] = []
            rules_by_block[block].append(rule)

        # Build nested output
        output = {}
        applied_targets: set[str] = set()

        for block_name, block_fields in blocks.items():
            rules = rules_by_block.get(block_name, [])
            if not rules:
                continue

            block_data = {}

            for rule in rules:
                source = rule.get("source")
                target = rule.get("target")
                transform = rule.get("transform")

                value = None
                if source and source in data:
                    value = data[source]

                    if transform:
                        value = self._apply_transform(transform, value, data, source_format)

                if value:
                    if target.startswith(block_name + "."):
                        relative_target = target[len(block_name) + 1 :]
                    else:
                        relative_target = target
                    self._set_nested(block_data, relative_target, value)
                    if target:
                        applied_targets.add(target)

            if block_data:
                output[block_name] = block_data

        # Compute missing fields — per-rule leaf-level entries
        missing_fields = []
        total_fields = 0
        applied_field_count = 0

        for rule in mapping.get("field_rules", []):
            target = rule.get("target", "")
            if not target:
                continue
            total_fields += 1
            if target in applied_targets:
                applied_field_count += 1
                continue
            level = "minimum" if rule.get("required") else "recommended"
            missing_fields.append(
                {
                    "field": target,
                    "level": level,
                    "description": f"{'Required' if level == 'minimum' else 'Recommended'} by {pivot_id} profile",
                }
            )

        # Also add block-level fields not covered by any rule (e.g. sourceRDI).
        # Skip if sub-rules exist — per-rule entries handle those individually.
        def _is_target_applied(t: str) -> bool:
            if t in applied_targets:
                return True
            prefix = t + "."
            return any(a.startswith(prefix) for a in applied_targets)

        rule_targets = {r.get("target", "") for r in mapping.get("field_rules", [])}
        for block_name, block_fields in blocks.items():
            for field in block_fields.get("required_fields", []):
                target_path = f"{block_name}.{field}"
                if target_path in rule_targets:
                    continue
                if any(t.startswith(target_path + ".") for t in rule_targets):
                    continue
                if not _is_target_applied(target_path):
                    missing_fields.append(
                        {
                            "field": target_path,
                            "level": "minimum",
                            "description": f"Required by {pivot_id} profile",
                        }
                    )
            for field in block_fields.get("recommended_fields", []):
                target_path = f"{block_name}.{field}"
                if target_path in rule_targets:
                    continue
                if any(t.startswith(target_path + ".") for t in rule_targets):
                    continue
                if not _is_target_applied(target_path):
                    missing_fields.append(
                        {
                            "field": target_path,
                            "level": "recommended",
                            "description": f"Recommended by {pivot_id} profile",
                        }
                    )

        confidence = round(applied_field_count / total_fields, 2) if total_fields else 1.0

        return {
            "json_ld": output,
            "field_rules": mapping.get("field_rules", []),
            "missing_fields": missing_fields,
            "confidence": confidence,
            "mapping_source": mapping_source,
            "model": self._last_mapping_model if mapping_source == "ai" else None,
        }

    def _apply_transform(
        self, transform_name: str, value: Any, data: dict, source_format: str
    ) -> Any:
        """Apply a named transform function."""
        # Look up transform from plugin
        plugin = self.plugins.get(source_format)
        if hasattr(plugin, transform_name):
            return getattr(plugin, transform_name)(value)
        return value

    def _set_nested(self, data: dict, path: str, value: Any) -> None:
        """Set a nested path in dict (e.g., "citation.title" = value)."""
        parts = path.split(".")
        current = data

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def get_mapping_info(self) -> dict:
        """Get info about the last mapping generation."""
        return {
            "ai_used": self._last_mapping_ai,
            "model": self._last_mapping_model,
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
