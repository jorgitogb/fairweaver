"""Build ARC scaffold directories from ARC RO-Crate JSON-LD using arctrl.

The builder maps Investigation/Study/Assay entities from an RO-Crate `@graph`
to arctrl Python objects and writes the full ARC scaffold (XLSX files and
directory tree) to disk. The intended consumer is the `POST /arc/scaffold`
endpoint in `main.py`.
"""

import io
import logging
import zipfile
from pathlib import Path
from typing import Any

from arctrl import (
    ARC,
    ArcAssay,
    ArcInvestigation,
    ArcStudy,
    ArcTable,
    Comment,
    CompositeCell,
    CompositeHeader,
    IOType,
    OntologyAnnotation,
    Person,
    Publication,
)

logger = logging.getLogger(__name__)


_ALLOWED_IDENTIFIER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ")


def sanitize_arc_identifier(value: Any) -> str:
    """Return an arctrl-safe identifier extracted from a raw value.

    The ARC specification and tooling accept only letters, digits, underscores,
    dashes and whitespace. If ``value`` looks like a URL or path, the last
    meaningful segment is used so the resulting folder name stays human-readable
    (e.g. ``https://doi.org/10.5447//2024/wheat-drought-001`` becomes
    ``wheat-drought-001``).
    """
    if not value:
        return "arc"

    text = str(value).strip()

    # Try to extract the last meaningful path segment from URLs or paths.
    segments = [seg.strip() for seg in text.replace("\\", "/").split("/") if seg.strip()]
    candidate = segments[-1] if segments else text

    # Keep only allowed characters, replacing everything else with a single space.
    sanitized = "".join(ch if ch in _ALLOWED_IDENTIFIER_CHARS else " " for ch in candidate)
    sanitized = " ".join(sanitized.split())

    return sanitized or "arc"


def build_scaffold_from_rocrate(rocrate_data: dict[str, Any], output_dir: Path) -> Path:
    """Build an ARC scaffold from parsed ARC RO-Crate data.

    Args:
        rocrate_data: Raw RO-Crate JSON dict containing a ``@graph`` list.
        output_dir: Directory where the scaffold will be written.

    Returns:
        Path to the written scaffold root.

    Raises:
        ValueError: If ``rocrate_data`` is missing ``@graph`` or contains no
            Investigation entity.
    """
    graph = rocrate_data.get("@graph", [])
    if not graph:
        raise ValueError("RO-Crate data must contain a non-empty @graph")

    investigation = _find_entity_by_type(graph, "Investigation")
    if investigation is None:
        raise ValueError("RO-Crate must contain at least one Investigation entity")

    studies = _find_all_by_type(graph, "Study")
    assays = _find_all_by_type(graph, "Assay")
    persons = _find_all_by_type(graph, "Person")
    arc = _build_arc(investigation, studies, assays, persons, graph)
    output_dir.mkdir(parents=True, exist_ok=True)
    arc.Write(str(output_dir))
    return output_dir


def _find_entity_by_type(graph: list[dict[str, Any]], type_name: str) -> dict[str, Any] | None:
    """Return the first entity whose ``@type`` or ``additionalType`` matches."""
    for entity in graph:
        if _entity_type_name(entity) == type_name:
            return entity
    return None


def _find_all_by_type(graph: list[dict[str, Any]], type_name: str) -> list[dict[str, Any]]:
    """Return all entities whose ``@type`` or ``additionalType`` matches."""
    return [e for e in graph if _entity_type_name(e) == type_name]


def _entity_type_name(entity: dict[str, Any]) -> str | None:
    """Extract the primary concrete type name from an entity.

    Prefers ``additionalType`` over ``@type`` when the latter is generic
    (e.g. ``Dataset`` with ``additionalType=Investigation``).
    """
    additional = entity.get("additionalType", [])
    if isinstance(additional, str):
        return additional
    if isinstance(additional, list) and additional:
        return additional[0]

    etype = entity.get("@type", [])
    if isinstance(etype, str):
        return etype
    if isinstance(etype, list) and etype:
        return etype[0]
    return None


def _build_arc(
    investigation: dict[str, Any],
    studies: list[dict[str, Any]],
    assays: list[dict[str, Any]],
    persons: list[dict[str, Any]],
    graph: list[dict[str, Any]],
) -> ARC:
    """Create an arctrl ARC from an RO-Crate Investigation entity."""
    raw_identifier = investigation.get("identifier") or investigation.get("@id", "arc")
    identifier = sanitize_arc_identifier(raw_identifier)

    person_by_id = {_local_id(p.get("@id", "")): _build_person(p) for p in persons}

    inv = ArcInvestigation(
        identifier=identifier,
        title=investigation.get("name"),
        description=investigation.get("description"),
        public_release_date=investigation.get("datePublished"),
    )
    inv.Contacts.extend(_linked_persons(investigation, person_by_id))
    inv.Publications.extend(_linked_publications(investigation, graph))

    # Investigation-level Comments
    _add_comment_if_exists(inv, investigation, "Investigation Keywords", "keywords")
    _add_comment_if_exists(inv, investigation, "Investigation Funding Agency", "funder")
    _add_comment_if_exists(inv, investigation, "Investigation Publisher", "publisher")
    _add_comment_if_exists(
        inv, investigation, "Investigation Alternative Title", "alternative_titles"
    )
    _add_comment_if_exists(inv, investigation, "Investigation URL", "url")
    _add_comment_if_exists(inv, investigation, "Investigation Version", "version")
    _add_comment_if_exists(inv, investigation, "Investigation Language", "inLanguage")

    arc_studies = [_add_study(inv, study, graph) for study in studies]
    study_by_id = {_local_id(s.get("@id", "")): study for s, study in zip(studies, arc_studies)}
    for arc_study, study in zip(arc_studies, studies):
        arc_study.Contacts.extend(_linked_persons(study, person_by_id))

    arc_assays: list[ArcAssay] = []
    for assay in assays:
        arc_assay = _add_assay(inv, assay, study_by_id)
        arc_assays.append(arc_assay)

    for arc_study, study in zip(arc_studies, studies):
        _add_study_tables(arc_study, study, graph)
    for arc_assay, assay in zip(arc_assays, assays):
        _add_assay_tables(arc_assay, assay, graph)

    return ARC.from_arc_investigation(inv)


def _add_study(
    inv: ArcInvestigation, study: dict[str, Any], graph: list[dict[str, Any]]
) -> ArcStudy:
    """Create and add an arctrl ArcStudy from an RO-Crate Study entity."""
    study_id = sanitize_arc_identifier(study.get("@id", "study"))
    arc_study = inv.InitStudy(study_id)
    arc_study.Title = study.get("name")
    arc_study.Description = study.get("description")
    arc_study.StudyDesignDescriptors.extend(_design_descriptors(study, graph))

    # Study-level Comments
    _add_comment_if_exists(arc_study, study, "Study Design Type", "studyDesignType")

    return arc_study


def _build_person(person: dict[str, Any]) -> Person:
    """Convert an RO-Crate Person entity to an arctrl Person."""
    orcid = ""
    raw_id = person.get("identifier", "")
    if isinstance(raw_id, dict):
        if raw_id.get("propertyID") == "orcid":
            orcid = raw_id.get("value", "")
        else:
            orcid = raw_id.get("@id", "")
    elif isinstance(raw_id, str):
        orcid = raw_id

    affiliation = ""
    raw_aff = person.get("affiliation", "")
    if isinstance(raw_aff, dict):
        affiliation = raw_aff.get("name", "")
    elif isinstance(raw_aff, str):
        affiliation = raw_aff

    return Person(
        first_name=person.get("givenName", ""),
        last_name=person.get("familyName", ""),
        email=person.get("email", ""),
        orcid=orcid,
        affiliation=affiliation,
    )


def _linked_persons(entity: dict[str, Any], person_by_id: dict[str, Person]) -> list[Person]:
    """Resolve Person references from fields such as creator/author/contact."""
    linked: list[Person] = []
    for key in (
        "creator",
        "author",
        "contact",
        "contributor",
        "investigationContacts",
        "studyPersonnel",
    ):
        for ref in _as_list(entity.get(key, [])):
            ref_id = ref if isinstance(ref, str) else ref.get("@id", "")
            person = person_by_id.get(_local_id(ref_id))
            if person is not None and person not in linked:
                linked.append(person)
    return linked


def _linked_publications(
    investigation: dict[str, Any], graph: list[dict[str, Any]]
) -> list[Publication]:
    """Resolve Publication references from investigationPublications."""
    pubs: list[Publication] = []
    for ref in _as_list(investigation.get("investigationPublications", [])):
        ref_id = ref if isinstance(ref, str) else ref.get("@id", "")
        entity = next((e for e in graph if _local_id(e.get("@id", "")) == _local_id(ref_id)), None)
        if entity is None:
            continue
        pub = Publication(
            doi=entity.get("identifier", ""),
            title=entity.get("name", ""),
            authors=_str_val(entity.get("authorList", "")),
        )
        if pub not in pubs:
            pubs.append(pub)
    return pubs


def _design_descriptors(
    study: dict[str, Any], graph: list[dict[str, Any]]
) -> list[OntologyAnnotation]:
    """Resolve OntologyAnnotation references from studyDesignDescriptors."""
    descriptors: list[OntologyAnnotation] = []
    for ref in _as_list(study.get("studyDesignDescriptors", [])):
        if isinstance(ref, str):
            oa = OntologyAnnotation(name=ref)
        elif isinstance(ref, dict):
            oa = OntologyAnnotation(
                name=ref.get("name", ""),
                tsr=ref.get("termSource", ""),
                tan=ref.get("termAccession", ""),
            )
        else:
            continue
        if oa not in descriptors:
            descriptors.append(oa)
    return descriptors


def _add_comment_if_exists(
    entity: ArcInvestigation | ArcStudy | ArcAssay,
    data: dict[str, Any],
    comment_name: str,
    field_name: str,
) -> None:
    """Add a Comment to an arctrl entity if the field exists and is non-empty."""
    value = _str_val(data.get(field_name))
    if value:
        entity.Comments.append(Comment(name=comment_name, value=value))


def _add_assay(
    inv: ArcInvestigation,
    assay: dict[str, Any],
    study_by_id: dict[str, ArcStudy],
) -> ArcAssay:
    """Create an arctrl ArcAssay and register it under the linked studies."""
    assay_id = sanitize_arc_identifier(assay.get("@id", "assay"))
    arc_assay = ArcAssay(
        identifier=assay_id,
        title=assay.get("name"),
        description=assay.get("description"),
        measurement_type=_ontology_annotation(assay.get("measurementTechnique")),
        technology_type=_ontology_annotation(assay.get("technologyType")),
        technology_platform=_ontology_annotation(assay.get("technologyPlatform")),
    )

    # Assay-level Comments
    _add_comment_if_exists(arc_assay, assay, "Assay Category", "assayCategory")
    _add_comment_if_exists(arc_assay, assay, "Assay Type", "assayType")

    target_studies = _linked_studies(assay, study_by_id)
    inv.AddAssay(arc_assay, register_in=target_studies or None)
    return arc_assay


def _parse_obo_uri(uri: str) -> tuple[str, str]:
    """Parse an OBO URI into (TermSourceREF, TermAccessionNumber).

    Example: http://purl.obolibrary.org/obo/NCBITaxon_4565 → (\"NCBITaxon\", \"NCBITaxon:4565\")
    """
    if not uri:
        return ("", "")
    if "obo/" in uri:
        part = uri.split("obo/")[-1]
        if "_" in part:
            tsr, tan_id = part.split("_", 1)
            return (tsr, f"{tsr}:{tan_id}")
    return ("", "")


def _term_cell(name: str, uri: str = "") -> CompositeCell:
    """Create a Term cell with optional ontology annotation."""
    if uri:
        tsr, tan = _parse_obo_uri(uri)
        return CompositeCell.create_term(OntologyAnnotation.create(name, tsr, tan))
    return CompositeCell.create_term(OntologyAnnotation.create(name))


def _coord_cell(value: float | None) -> CompositeCell:
    """Create a Unitized cell for a geographic coordinate."""
    if value is None:
        return CompositeCell.create_term(OntologyAnnotation.create(""))
    return CompositeCell.create_unitized(
        str(value),
        OntologyAnnotation.create("degree", "UO", "UO:0000185"),
    )


def _find_root(graph: list[dict]) -> dict:
    return next((e for e in graph if e.get("@id") == "./"), {})


def _resolve_ref(graph: list[dict], ref: Any) -> dict | None:
    """Resolve a @id reference to the entity in the graph."""
    if isinstance(ref, dict) and ref.get("@id"):
        return next((e for e in graph if e.get("@id") == ref["@id"]), None)
    return None


def _add_study_tables(arc_study: ArcStudy, study: dict[str, Any], graph: list[dict]) -> None:
    """Add annotation tables (plant_material, drought_treatment) to a study."""
    crop_species = study.get("crop_species", "")
    crop_species_uri = study.get("crop_species_uri", "")
    crop_pest = study.get("crop_pest", "")
    crop_pest_uri = study.get("crop_pest_uri", "")

    root = _find_root(graph)
    lat = None
    lng = None
    country = None
    location_entity = _resolve_ref(graph, root.get("location"))
    if location_entity:
        geo = location_entity.get("geo", {})
        if isinstance(geo, dict):
            lat = geo.get("latitude")
            lng = geo.get("longitude")
    coverage_entity = _resolve_ref(graph, root.get("geographicCoverage"))
    if coverage_entity:
        country = coverage_entity.get("country")
    soil_entity = _resolve_ref(graph, root.get("soil"))
    soil_name = soil_entity.get("name", "") if soil_entity else ""
    process_entity = _resolve_ref(graph, root.get("process"))
    process_name = process_entity.get("name", "") if process_entity else ""

    # ── Table: plant_material (Sources → Samples) ──
    has_plant_data = any([crop_species, crop_pest, lat is not None, country])
    if has_plant_data:
        headers = [
            CompositeHeader.input(IOType.source()),
            CompositeHeader.characteristic(OntologyAnnotation.create("Organism")),
            CompositeHeader.characteristic(
                OntologyAnnotation.create("geographic location (latitude)")
            ),
            CompositeHeader.characteristic(
                OntologyAnnotation.create("geographic location (longitude)")
            ),
            CompositeHeader.characteristic(
                OntologyAnnotation.create("geographic location (country)")
            ),
            CompositeHeader.output(IOType.sample()),
        ]
        cells = [
            CompositeCell.create_free_text("Source_1"),
            _term_cell(crop_species, crop_species_uri),
            _coord_cell(lat),
            _coord_cell(lng),
            _term_cell(country if country else ""),
            CompositeCell.create_free_text("Sample_1"),
        ]
        if crop_pest:
            headers.insert(
                2,
                CompositeHeader.characteristic(OntologyAnnotation.create("Infection Taxon")),
            )
            cells.insert(2, _term_cell(crop_pest, crop_pest_uri))
        if soil_name:
            headers.insert(
                -1,
                CompositeHeader.characteristic(OntologyAnnotation.create("soil type")),
            )
            cells.insert(-1, _term_cell(soil_name))

        table = ArcTable.create_from_rows("plant_material", headers, [cells])
        arc_study.AddTable(table)

    # ── Table: drought_treatment (Samples → Samples) ──
    treatment_headers = [
        CompositeHeader.input(IOType.sample()),
        CompositeHeader.parameter(OntologyAnnotation.create("irrigation regime")),
        CompositeHeader.parameter(OntologyAnnotation.create("water amount")),
        CompositeHeader.output(IOType.sample()),
    ]
    treatment_rows = [
        [
            CompositeCell.create_free_text("Sample_1"),
            _term_cell("full irrigation"),
            CompositeCell.create_unitized(
                "100", OntologyAnnotation.create("percent", "UO", "UO:0000187")
            ),
            CompositeCell.create_free_text("Sample_1_treated"),
        ],
        [
            CompositeCell.create_free_text("Sample_2"),
            _term_cell("reduced irrigation"),
            CompositeCell.create_unitized(
                "50", OntologyAnnotation.create("percent", "UO", "UO:0000187")
            ),
            CompositeCell.create_free_text("Sample_2_treated"),
        ],
        [
            CompositeCell.create_free_text("Sample_3"),
            _term_cell("rain-fed control"),
            CompositeCell.create_unitized(
                "0", OntologyAnnotation.create("percent", "UO", "UO:0000187")
            ),
            CompositeCell.create_free_text("Sample_3_treated"),
        ],
    ]
    if process_name:
        pheader = CompositeHeader.parameter(OntologyAnnotation.create("process type"))
        treatment_headers.insert(-1, pheader)
        for row in treatment_rows:
            row.insert(-1, _term_cell(process_name))

    table = ArcTable.create_from_rows("drought_treatment", treatment_headers, treatment_rows)
    arc_study.AddTable(table)


def _add_assay_tables(arc_assay: ArcAssay, assay: dict[str, Any], graph: list[dict]) -> None:
    """Add annotation table (multispectral_imaging) to an assay."""
    meas_technique = _str_val(assay.get("measurementTechnique"))
    meas_method = _str_val(assay.get("measurementMethod"))
    tech_type = _str_val(assay.get("technologyType"))
    tech_platform = _str_val(assay.get("technologyPlatform"))

    if not meas_technique and not tech_type:
        return

    headers = [
        CompositeHeader.input(IOType.sample()),
        CompositeHeader.parameter(OntologyAnnotation.create("measurement technique")),
        CompositeHeader.parameter(OntologyAnnotation.create("measurement method")),
        CompositeHeader.parameter(OntologyAnnotation.create("technology type")),
        CompositeHeader.parameter(OntologyAnnotation.create("technology platform")),
        CompositeHeader.output(IOType.data()),
    ]
    rows = [
        [
            CompositeCell.create_free_text("Sample_1_treated"),
            _term_cell(meas_technique),
            _term_cell(meas_method if meas_method else meas_technique),
            _term_cell(tech_type if tech_type else meas_technique),
            _term_cell(tech_platform if tech_platform else ""),
            CompositeCell.create_data_from_string("sample1.tiff", "", ""),
        ],
        [
            CompositeCell.create_free_text("Sample_2_treated"),
            _term_cell(meas_technique),
            _term_cell(meas_method if meas_method else meas_technique),
            _term_cell(tech_type if tech_type else meas_technique),
            _term_cell(tech_platform if tech_platform else ""),
            CompositeCell.create_data_from_string("sample2.tiff", "", ""),
        ],
        [
            CompositeCell.create_free_text("Sample_3_treated"),
            _term_cell(meas_technique),
            _term_cell(meas_method if meas_method else meas_technique),
            _term_cell(tech_type if tech_type else meas_technique),
            _term_cell(tech_platform if tech_platform else ""),
            CompositeCell.create_data_from_string("sample3.tiff", "", ""),
        ],
    ]

    table = ArcTable.create_from_rows("multispectral_imaging", headers, rows)
    arc_assay.AddTable(table)


def _linked_studies(assay: dict[str, Any], study_by_id: dict[str, ArcStudy]) -> list[ArcStudy]:
    """Resolve the Studies an Assay is ``about`` or has as parent."""
    linked: list[ArcStudy] = []
    for key in ("about", "isPartOf"):
        for ref in _as_list(assay.get(key, [])):
            ref_id = ref if isinstance(ref, str) else ref.get("@id", "")
            study = study_by_id.get(_local_id(ref_id))
            if study is not None and study not in linked:
                linked.append(study)
    return linked


def _str_val(val: Any) -> str:
    """Extract string value from a raw field (may be dict with @id ref, DefinedTerm ref, or plain string)."""
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        # Join list items with semicolons (ISA standard for multiple values)
        return "; ".join(_str_val(item) for item in val if _str_val(item))
    if isinstance(val, dict):
        if "name" in val:
            return val["name"]
        if "@id" in val:
            return val["@id"]
    return ""


def _ontology_annotation(value: Any) -> OntologyAnnotation | None:
    """Wrap a string value as an arctrl OntologyAnnotation."""
    if not value:
        return None
    if isinstance(value, str):
        return OntologyAnnotation(name=value)
    if isinstance(value, dict):
        return OntologyAnnotation(
            name=value.get("name", ""),
            tsr=value.get("termSource", ""),
            tan=value.get("termAccession", ""),
        )
    return None


def zip_scaffold(scaffold_dir: Path, arc_name: str) -> bytes:
    """Package a generated ARC scaffold directory into a ZIP archive.

    Args:
        scaffold_dir: Path to the scaffold root.
        arc_name: Directory name to use inside the ZIP.

    Returns:
        Raw ZIP file bytes.
    """
    buffer = io.BytesIO()
    arc_root = Path(arc_name)
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(scaffold_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arc_root / path.relative_to(scaffold_dir))
    return buffer.getvalue()


def _local_id(entity_id: str) -> str:
    """Return a filesystem-friendly identifier from an ``@id`` value.

    Removes common RO-Crate prefixes such as ``#`` and ``./``.
    """
    if not isinstance(entity_id, str):
        return "id"
    return entity_id.lstrip("#").lstrip("./").strip() or "id"


def _as_list(value: Any) -> list[Any]:
    """Normalize a value to a list (single item becomes a one-element list)."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
