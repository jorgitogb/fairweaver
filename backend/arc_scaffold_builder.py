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

from arctrl import ARC, ArcAssay, ArcInvestigation, ArcStudy, OntologyAnnotation, Person

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
    arc = _build_arc(investigation, studies, assays, persons)
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

    arc_studies = [_add_study(inv, study) for study in studies]
    study_by_id = {_local_id(s.get("@id", "")): study for s, study in zip(studies, arc_studies)}
    for arc_study, study in zip(arc_studies, studies):
        arc_study.Contacts.extend(_linked_persons(study, person_by_id))

    for assay in assays:
        _add_assay(inv, assay, study_by_id)

    return ARC.from_arc_investigation(inv)


def _add_study(inv: ArcInvestigation, study: dict[str, Any]) -> ArcStudy:
    """Create and add an arctrl ArcStudy from an RO-Crate Study entity."""
    study_id = _local_id(study.get("@id", "study"))
    arc_study = inv.InitStudy(study_id)
    arc_study.Title = study.get("name")
    arc_study.Description = study.get("description")
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
    for key in ("creator", "author", "contact", "contributor"):
        for ref in _as_list(entity.get(key, [])):
            ref_id = ref if isinstance(ref, str) else ref.get("@id", "")
            person = person_by_id.get(_local_id(ref_id))
            if person is not None and person not in linked:
                linked.append(person)
    return linked


def _add_assay(
    inv: ArcInvestigation,
    assay: dict[str, Any],
    study_by_id: dict[str, ArcStudy],
) -> None:
    """Create an arctrl ArcAssay and register it under the linked studies."""
    assay_id = _local_id(assay.get("@id", "assay"))
    arc_assay = ArcAssay(
        identifier=assay_id,
        title=assay.get("name"),
        description=assay.get("description"),
        measurement_type=_ontology_annotation(assay.get("measurementTechnique")),
        technology_type=_ontology_annotation(assay.get("technologyType")),
        technology_platform=_ontology_annotation(assay.get("technologyPlatform")),
    )

    target_studies = _linked_studies(assay, study_by_id)
    inv.AddAssay(arc_assay, register_in=target_studies or None)


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
