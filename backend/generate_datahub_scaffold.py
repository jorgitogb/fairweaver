"""Generate a DataHub-ready ARC scaffold from an ARC RO-Crate JSON-LD file.

This script wraps ``arc_scaffold_builder.build_scaffold_from_rocrate`` with
additional DataHub conveniences:

- Placeholder data files for every ``File`` entity referenced in the RO-Crate
  (so the assay ``dataset/`` folder is not empty).
- A LICENSE file copied from the RO-Crate ``license`` field.
- A copy of the original ``ro-crate-metadata.json`` for reference.

Usage:

    uv run python generate_datahub_scaffold.py \
        ../sample-data/demo/arc-ro-crate-wheat-full.json \
        ../sample-data/demo/arc-scaffold-wheat-drought

"""

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from arc_scaffold_builder import build_scaffold_from_rocrate

logger = logging.getLogger(__name__)

_CC_BY_4 = """Creative Commons Attribution 4.0 International Public License

By exercising the Licensed Rights (defined below), You accept and agree to be
bound by the terms and conditions of this Creative Commons Attribution 4.0
International Public License ("Public License"). To the extent this Public
License may be interpreted as a contract, You are granted the Licensed Rights
in consideration of Your acceptance of these terms and conditions, and the
Licensor grants You such rights in consideration of benefits the Licensor
receives from making the Licensed Material available under these terms and
conditions.

Full text: https://creativecommons.org/licenses/by/4.0/legalcode
"""

_TIFF_HEADER = b"II\x2a\x00\x08\x00\x00\x00"


def _file_entities(rocrate_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all File entities from the RO-Crate graph."""
    graph = rocrate_data.get("@graph", [])
    return [e for e in graph if _entity_type_name(e) == "File"]


def _entity_type_name(entity: dict[str, Any]) -> str | None:
    """Extract the primary type name from an entity."""
    etype = entity.get("@type", [])
    if isinstance(etype, str):
        return etype
    if isinstance(etype, list) and etype:
        return etype[0]
    return None


def _assay_folders(scaffold_dir: Path) -> list[str]:
    """Return the names of assay folders created by arctrl."""
    assays_dir = scaffold_dir / "assays"
    if not assays_dir.exists():
        return []
    return [p.name for p in assays_dir.iterdir() if p.is_dir() and p.name != ".gitkeep"]


def _add_placeholder_data_files(
    rocrate_data: dict[str, Any],
    scaffold_dir: Path,
) -> None:
    """Create placeholder files in the arctrl assay dataset folders.

    File entity IDs are mapped to the first available assay folder so the
    data is reachable by ARC tooling. Files are written with a minimal TIFF
    header so MIME detection works, while keeping the size tiny.
    """
    assay_folders = _assay_folders(scaffold_dir)
    if not assay_folders:
        logger.warning("No assay folders found; skipping placeholder data files")
        return

    for entity in _file_entities(rocrate_data):
        file_id = entity.get("@id", "")
        if not file_id:
            continue

        # File IDs may be full paths (e.g. assays/wheat/dataset/sample.tiff).
        # Rebase them under the actual arctrl assay folder for DataHub.
        path = Path(file_id)
        file_name = path.name
        target = scaffold_dir / "assays" / assay_folders[0] / "dataset" / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_TIFF_HEADER)
        logger.info("Created placeholder data file: %s", target.relative_to(scaffold_dir))


def _find_root_dataset(graph: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the RO-Crate root Dataset entity (``@id`` == ``./``)."""
    for entity in graph:
        if entity.get("@id") == "./":
            return entity
    return None


def _add_license_file(
    rocrate_data: dict[str, Any],
    scaffold_dir: Path,
) -> None:
    """Write a LICENSE file based on the RO-Crate root Dataset license field."""
    graph = rocrate_data.get("@graph", [])
    root = _find_root_dataset(graph) or {}
    license_url = root.get("license", "")
    if not isinstance(license_url, str):
        license_url = ""

    if "creativecommons.org/licenses/by/4.0" in license_url:
        text = _CC_BY_4
    else:
        text = f"License: {license_url or 'not specified'}\n"

    license_path = scaffold_dir / "LICENSE"
    license_path.write_text(text)
    logger.info("Created LICENSE file: %s", license_path.relative_to(scaffold_dir))


def generate_datahub_scaffold(
    source_path: Path,
    output_dir: Path,
) -> Path:
    """Build and decorate a DataHub-ready ARC scaffold."""
    with open(source_path) as f:
        rocrate_data = json.load(f)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    build_scaffold_from_rocrate(rocrate_data, output_dir)
    _add_placeholder_data_files(rocrate_data, output_dir)
    _add_license_file(rocrate_data, output_dir)

    # Keep original RO-Crate alongside the scaffold for reference / diff.
    shutil.copy2(source_path, output_dir / "ro-crate-metadata.json")
    logger.info("Copied source RO-Crate to %s", output_dir / "ro-crate-metadata.json")

    return output_dir


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Generate a DataHub-ready ARC scaffold from an RO-Crate file."
    )
    parser.add_argument("source", type=Path, help="Path to ARC RO-Crate JSON-LD file")
    parser.add_argument("output", type=Path, help="Directory where the scaffold will be written")
    args = parser.parse_args()

    generate_datahub_scaffold(args.source, args.output)
    print(f"Scaffold written to: {args.output}")


if __name__ == "__main__":
    main()
