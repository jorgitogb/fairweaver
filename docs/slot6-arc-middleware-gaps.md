# Slot 6: ARC-based Middleware — Gaps & Observations

**Presenters:** Jorge & Julian

---

## Slide 1: Metadata Blocks We Don't Account For

### Missing from current middleware pipeline:

| Block | Impact | Status |
|-------|--------|--------|
| **Provenance** (`wasGeneratedBy`, `wasDerivedFrom`) | Traceability of data origin | Not captured |
| **Licensing** (beyond `$licenseURL` placeholder) | Legal compliance | Placeholder only |
| **Temporal Coverage** (`temporalCoverage`) | Time range of observations | Not modeled |
| **Spatial Resolution** (`spatialResolutionInMeters`) | Granularity of location data | Not captured |
| **Variable Measured** (`variableMeasured`) | Core scientific content | Partial (only keywords) |
| **Distribution** (`distribution`) | Access URLs, file formats | Not modeled |
| **Conforms To** (profiles beyond Bioschemas) | Standards compliance | Bioschemas only |
| **Contact Point** (`contactPoint`) | Data steward info | Not captured |
| **Funding** (`funding`) | Grant attribution | Not modeled |
| **Citation** (`citation`) | Academic credit | Not captured |

### From ARC demo files — fields present but not indexed:

| Field | Wheat Full | Maize Full | Search Hub Index |
|-------|------------|------------|------------------|
| `funder` | "DFG" | — | No |
| `investigationContacts` | 2 persons | — | No |
| `investigationPublications` | 1 article | — | No |
| `crop_species` | "Triticum aestivum" | — | No |
| `crop_species_uri` | NCBITaxon_4565 | — | No |
| `studyDesignType` | "RCBD" | — | No |
| `studyDesignDescriptors` | 7 keywords | — | No |
| `soil.type` | "Luvisol" | — | No |
| `process.type` | "UAV remote sensing" | — | No |

---

## Slide 2: New Possible Detections in Real ARCs

### ARC complexity tiers (from demo data):

| Tier | Entities | Fields | Example |
|------|----------|--------|---------|
| **Basic** | Investigation → Study → Assay | ~15 | `arc-ro-crate-wheat-basic.json` |
| **Intermediate** | + keywords, design, assay metadata | ~25 | `arc-ro-crate-wheat-intermediate.json` |
| **Full** | + location, soil, process, publications | ~40 | `arc-ro-crate-wheat-full.json` |
| **Real-world** | All above + embedded data | 100+ | `arc-ro-crate-benjamin.json` |

### Entity-level coverage gaps:

| ARC Entity | Basic | Intermediate | Full | Missing in Basic |
|------------|-------|--------------|------|------------------|
| Investigation | name, desc, identifier | + keywords, publisher | + funder, contacts, publications | keywords, funder |
| Study | name, desc | + design type, personnel | + crop, pest, descriptors | experimental design |
| Assay | name, measurementTechnique | + assayCategory, assayType | + instrument | instrument details |
| Location | — | — | name, geo coordinates | All (critical gap) |
| GeographicCoverage | — | — | country, state, county | All |
| Soil | — | — | soil type | All |
| Process | — | — | process type | All |
| Publication | — | — | name, DOI, authors | All |

### New field types discovered:

| Field | Type | Extraction Complexity |
|-------|------|----------------------|
| `identifier` (nested) | `PropertyValue` with ORCID | High — nested JSON |
| `affiliation` | `Organization` object | Medium — nested object |
| `geo` | `GeoCoordinates` (lat/lng) | Low — direct mapping |
| `crop_species_uri` | OBO ontology URI | High — requires validation |
| `measurementMethod` | Free text | Low — direct mapping |
| `technologyPlatform` | Free text | Low — direct mapping |

---

## Slide 3: ARC Metadata Size Analysis

### Measured file sizes (demo folder):

| File | Tier | Size | Lines | Entities |
|------|------|------|-------|----------|
| `arc-ro-crate-wheat-basic.json` | Basic | **4.6 KB** | 142 | 8 |
| `arc-ro-crate-maize-basic.json` | Basic | **5.2 KB** | 165 | 8 |
| `arc-ro-crate-wheat-intermediate.json` | Intermediate | **5.3 KB** | 171 | 10 |
| `arc-ro-crate-maize-intermediate.json` | Intermediate | **5.9 KB** | — | 10 |
| `arc-ro-crate-wheat-full.json` | Full | **7.6 KB** | 256 | 14 |
| `arc-ro-crate-maize-full.json` | Full | **8.2 KB** | — | 14 |
| `arc-ro-crate-wheat-danielA.json` | Real | **42 KB** | — | 50+ |
| `arc-ro-crate-benjamin.json` | Real | **103 MB** | — | 1000+ |
| `arc-ro-crate-metadata-matthiasL.json` | Real | **371 MB** | — | 1000+ |

### Size progression by enrichment level:

```
Basic:           4.6 KB  ████░░░░░░░░░░░░░░░░  (baseline)
Intermediate:    5.3 KB  █████░░░░░░░░░░░░░░░  (+15%)
Full:            7.6 KB  ████████░░░░░░░░░░░░  (+65%)
Real (Daniel):  42 KB    ████████████████████  (+813%)
Real (Benjamin): 103 MB  ████████████████████  (+2,238,000%)
```

### Size breakdown (wheat-full example, 7.6 KB):

| Component | Size | % | Fields |
|-----------|------|---|--------|
| Root Dataset | 0.8 KB | 10% | name, description, creator refs |
| Person entities (×2) | 1.2 KB | 16% | name, email, ORCID, affiliation |
| Investigation | 1.4 KB | 18% | keywords, funder, publications |
| Study | 0.9 KB | 12% | design type, personnel, crop |
| Assay | 0.7 KB | 9% | technique, method, instrument |
| Location | 0.3 KB | 4% | name, geo coordinates |
| GeographicCoverage | 0.3 KB | 4% | country, state, county |
| Soil + Process | 0.2 KB | 3% | type names |
| Publication | 0.4 KB | 5% | name, DOI, authors |
| File refs (×3) | 0.3 KB | 4% | name, encodingFormat |
| RO-Crate metadata | 0.2 KB | 3% | conformsTo, about |
| **Overhead (IDs, refs)** | **0.9 KB** | **12%** | `@id` references |

### Key observations:

1. **Bloat factor:** Real ARCs (Benjamin: 103 MB) are **22,000x larger** than basic ARCs
2. **Entity duplication:** Same description repeated at Investigation, Study, and root level
3. **ID overhead:** `@id` references consume ~12% of file size in full ARCs
4. **Scalability concern:** 1000 datasets × 8 KB = 8 MB per harvest cycle
5. **Compression potential:** Deduplication + normalization could reduce by ~40%

### Implications for Search Hub:

| Metric | Value |
|--------|-------|
| Basic harvest (100 datasets) | ~0.5 MB |
| Full harvest (100 datasets) | ~0.8 MB |
| Real harvest (100 datasets) | ~10 GB (if full metadata) |
| **Recommendation** | Harvest full, index selectively, compress IDs |

---

## Summary: Action Items

1. **Expand format plugins** to capture provenance, licensing, and variable metadata
2. **Implement entity deduplication** to reduce Investigation/Study/Root description redundancy
3. **Add ORCID extraction** from nested `PropertyValue` objects
4. **Model missing ARC entities** (Location, Soil, Process, Publication)
5. **Define metadata pruning strategy** — index basic fields, store full for on-demand
6. **Implement compression** — flatten ID references, normalize repeated strings