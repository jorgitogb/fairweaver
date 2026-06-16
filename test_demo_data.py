#!/usr/bin/env python3
"""Tests for FAIRagro Demo Suite: mock data validation and compliance classification."""
import json, os, sys
from pathlib import Path
import warnings

HERE = Path(__file__).parent
DEMO = HERE / "sample-data" / "demo"


def test_demo_files_exist():
    """All 12 demo files exist."""
    themes = ["wheat", "maize"]
    levels = ["basic", "intermediate", "full"]
    for theme in themes:
        for level in levels:
            so = DEMO / f"schema-org-{theme}-{level}.json"
            arc = DEMO / f"arc-ro-crate-{theme}-{level}.json"
            assert so.exists(), f"Missing: {so}"
            assert arc.exists(), f"Missing: {arc}"


def test_schema_org_files_are_valid_json():
    """All Schema.org files parse as valid JSON with correct structure."""
    themes = ["wheat", "maize"]
    levels = ["basic", "intermediate", "full"]
    for theme in themes:
        for level in levels:
            path = DEMO / f"schema-org-{theme}-{level}.json"
            with open(path) as f:
                d = json.load(f)
            assert d.get("@context") == "https://schema.org", f"{path}: missing @context"
            assert d.get("@type") == "Dataset", f"{path}: missing @type"
            assert d.get("name"), f"{path}: missing name"
            assert d.get("description"), f"{path}: missing description"


def test_arc_files_are_valid_json():
    """All ARC files parse as valid JSON with RO-Crate structure."""
    themes = ["wheat", "maize"]
    levels = ["basic", "intermediate", "full"]
    for theme in themes:
        for level in levels:
            path = DEMO / f"arc-ro-crate-{theme}-{level}.json"
            with open(path) as f:
                d = json.load(f)
            assert "@graph" in d, f"{path}: missing @graph"
            assert len(d["@graph"]) > 0, f"{path}: empty @graph"
            # Check required entities
            types_in_graph = set()
            for e in d["@graph"]:
                at = e.get("additionalType", e.get("@type", ""))
                if isinstance(at, list):
                    types_in_graph.update(at)
                else:
                    types_in_graph.add(at)
            for entity in ["Investigation", "Study", "Assay"]:
                assert entity in types_in_graph, f"{path}: missing {entity}"


def test_arc_basic_has_minimal_fields():
    """Basic ARC files only have required fields, no extras."""
    for theme in ["wheat", "maize"]:
        path = DEMO / f"arc-ro-crate-{theme}-basic.json"
        with open(path) as f:
            d = json.load(f)
        for e in d["@graph"]:
            at = e.get("additionalType", "")
            if at == "Investigation":
                assert "keywords" not in e, f"{path}: Investigation has keywords (should be basic only)"
                assert "funder" not in e, f"{path}: Investigation has funder (should be basic)"
            if at == "Assay":
                assert "sensorType" not in e, f"{path}: Assay has sensorType (should be basic)"


def test_arc_full_has_advanced_fields():
    """Full ARC files have publishable/reproducible/fairagro fields."""
    for theme in ["wheat", "maize"]:
        path = DEMO / f"arc-ro-crate-{theme}-full.json"
        with open(path) as f:
            d = json.load(f)
        found_investigation = False
        found_publication = False
        for e in d["@graph"]:
            at = e.get("additionalType", e.get("@type", ""))
            if at == "Investigation":
                found_investigation = True
                assert "funder" in e, f"{path}: Missing funder"
                assert "alternative_titles" in e, f"{path}: Missing alternative_titles"
            if at == "ScholarlyArticle":
                found_publication = True
        assert found_publication, f"{path}: Missing ScholarlyArticle publication"


def test_compliance_classification():
    """Compliance classification assigns correct levels."""
    sys.path.insert(0, str(HERE / "backend"))
    import os
    os.chdir(str(HERE / "backend"))
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    themes = {"wheat": "wheat", "maize": "maize"}
    for theme_key, theme_label in themes.items():
        for level in ["basic", "intermediate", "full"]:
            path = DEMO / f"schema-org-{theme_key}-{level}.json"
            with open(path, "rb") as f:
                resp = client.post("/compliance/classify", files={"file": (path.name, f, "application/json")})
            assert resp.status_code == 200, f"{path.name}: {resp.status_code}"
            data = resp.json()
            assert data["level"] == level, f"{path.name}: expected {level}, got {data['level']}"


def _make_validator():
    sys.path.insert(0, str(HERE / "backend"))
    from arc_templates.fairagro_validator import FairagroArcValidator
    return FairagroArcValidator()


def test_arc_basic_passes_validator():
    """Basic ARC files pass FairagroArcValidator at basic level."""
    validator = _make_validator()
    for theme in ["wheat", "maize"]:
        path = DEMO / f"arc-ro-crate-{theme}-basic.json"
        with open(path) as f:
            d = json.load(f)
        result = validator.validate(d)
        assert "valid" in result


def test_arc_full_passes_validator():
    """Full ARC files pass all FairagroArcValidator checks."""
    validator = _make_validator()
    for theme in ["wheat", "maize"]:
        path = DEMO / f"arc-ro-crate-{theme}-full.json"
        with open(path) as f:
            d = json.load(f)
        result = validator.validate(d)
        assert "valid" in result, f"{path}: validator failed"
