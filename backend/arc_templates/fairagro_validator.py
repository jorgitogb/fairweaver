from typing import Any, List, Dict
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FairagroArcValidator:
    """Validates ARC RO-Crate against FAIRagro template and DataPLANT ARC specification."""

    def __init__(self, template_path: str = None):
        self.template = self._load_template(template_path)

    def _load_template(self, template_path: str) -> Dict:
        """Load FAIRagro ARC template."""
        if template_path is None:
            template_path = Path(__file__).parent / "fairagro_template.yaml"
        try:
            with open(template_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse template YAML: {e}")
            raise

    def validate(self, arc_data: Dict[str, Any]) -> Dict:
        """Validate ARC data against FAIRagro template and DataPLANT specification."""
        errors = []
        warnings = []
        graph = arc_data.get("@graph", [])

        # 1. Validate ARC directory structure (if file system access available)
        self._validate_arc_structure(errors, warnings)

        # 2. Check required entities
        for entity_type in self.template["required_entities"]:
            found = any(self._has_type(e, entity_type) for e in graph)
            if not found:
                errors.append(f"Missing required entity: {entity_type}")

        # 3. Check required fields
        for entity_type, required_fields in self.template["required_fields"].items():
            entity_instances = [e for e in graph if self._has_type(e, entity_type)]
            for entity in entity_instances:
                for field in required_fields:
                    if field not in entity:
                        errors.append(
                            f"{entity_type} {entity.get('@id', 'unknown')} missing required field: {field}"
                        )

        # 4. Check validation rules
        for rule in self.template.get("validation_rules", []):
            self._check_validation_rule(rule, graph, errors, warnings)

        # 5. Check DataPLANT ARC requirements
        self._validate_dataplant_requirements(arc_data, errors, warnings)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "template_id": self.template["template_id"],
            "template_version": self.template["version"],
            "compliance": {
                "dataplant_arc": self._check_dataplant_compliance(errors),
                "fairagro": self._check_fairagro_compliance(errors),
                "publishable": self._check_publishable_compliance(errors, warnings),
            },
        }

    def _validate_arc_structure(self, errors: List, warnings: List):
        """Validate ARC directory structure (DataPLANT ARC Specification)."""
        try:
            # This would require file system access to the ARC directory
            # For now, we'll skip this in the JSON-only validator
            # In a full implementation, this would check:
            # - Required directories exist (.arc, studies, assays, workflows, runs)
            # - Required files exist (isa.investigation.xlsx, ro-crate-metadata.json)
            warnings.append("ARC structure validation skipped (requires file system access)")
        except Exception as e:
            errors.append(f"ARC structure validation failed: {str(e)}")

    def _validate_dataplant_requirements(self, arc_data: Dict, errors: List, warnings: List):
        """Validate DataPLANT-specific ARC requirements."""
        graph = arc_data.get("@graph", [])

        # Check for investigation metadata file
        investigation_file = next(
            (e for e in graph if e.get("@id") == "isa.investigation.xlsx"), None
        )
        if not investigation_file:
            errors.append("Missing required file: isa.investigation.xlsx")

        # Check for RO-Crate metadata file
        ro_crate_file = next((e for e in graph if e.get("@id") == "ro-crate-metadata.json"), None)
        if not ro_crate_file:
            errors.append("Missing required file: ro-crate-metadata.json")

        # Check investigation has required metadata for publishable ARC
        investigation = next((e for e in graph if self._has_type(e, "Investigation")), None)
        if investigation:
            required_metadata = ["name", "description", "identifier", "license", "datePublished"]
            missing_metadata = [field for field in required_metadata if field not in investigation]
            if missing_metadata:
                warnings.append(
                    f"Investigation missing recommended metadata for publishable ARC: {', '.join(missing_metadata)}"
                )

    def _check_validation_rule(self, rule: Dict, graph: List, errors: List, warnings: List):
        """Check individual validation rules."""
        rule_type = rule["type"]

        if rule_type == "required":
            self._check_required_rule(rule, graph, errors)
        elif rule_type == "at_least_one":
            self._check_at_least_one_rule(rule, graph, errors)
        elif rule_type == "directory_structure":
            self._check_directory_structure_rule(rule, errors)
        elif rule_type == "file_existence":
            self._check_file_existence_rule(rule, errors)
        elif rule_type == "required_fields":
            self._check_required_fields_rule(rule, graph, errors)
        elif rule_type == "path_resolution":
            self._check_path_resolution_rule(rule, graph, warnings)
        else:
            warnings.append(f"Unknown validation rule type: {rule_type}")

    def _check_directory_structure_rule(self, rule: Dict, errors: List):
        """Check directory structure rule."""
        # This would require file system access
        # For JSON-only validation, we'll skip this
        pass

    def _check_file_existence_rule(self, rule: Dict, errors: List):
        """Check file existence rule."""
        # This would require file system access
        # For JSON-only validation, we'll skip this
        pass

    def _check_required_fields_rule(self, rule: Dict, graph: List, errors: List):
        """Check required fields rule."""
        entity_type = rule["path"]
        fields = rule["fields"]
        entities = [e for e in graph if self._has_type(e, entity_type)]
        for entity in entities:
            missing_fields = [field for field in fields if field not in entity]
            if missing_fields:
                errors.append(
                    f"{entity_type} {entity.get('@id', 'unknown')} missing required fields: {', '.join(missing_fields)}"
                )

    def _check_path_resolution_rule(self, rule: Dict, graph: List, warnings: List):
        """Check data path resolution rule."""
        # This would require file system access to resolve paths
        # For JSON-only validation, we'll skip this
        pass

    def _check_required_rule(self, rule: Dict, graph: List, errors: List):
        """Check required field rule."""
        path = rule["path"]
        # Handle multiple field options (e.g., "Investigation.creator | Investigation.investigationContacts")
        field_options = [opt.strip() for opt in path.split("|")]

        for field_opt in field_options:
            if "/" in field_opt:  # Entity.field format
                entity_type, field = field_opt.split(".")
                entities = [e for e in graph if self._has_type(e, entity_type)]
                for entity in entities:
                    if field not in entity:
                        errors.append(f"{entity_type} missing required field: {field}")

    def _check_at_least_one_rule(self, rule: Dict, graph: List, errors: List):
        """Check at least one of multiple fields rule."""
        paths = rule["path"].split(", ")
        entity_type = paths[0].split(".")[0]
        fields = [p.split(".")[1] for p in paths]
        entities = [e for e in graph if self._has_type(e, entity_type)]
        for entity in entities:
            has_any = any(field in entity for field in fields)
            if not has_any:
                errors.append(f"{entity_type} requires at least one of: {', '.join(fields)}")

    def _has_type(self, entity: Dict, type_name: str) -> bool:
        """Check if entity has the specified type."""
        if not isinstance(entity, dict):
            return False
        atype = entity.get("@type", [])
        if isinstance(atype, str):
            atype = [atype]
        if type_name in atype:
            return True
        # Also check additionalType (ARC uses @type=Dataset + additionalType=Investigation)
        atype2 = entity.get("additionalType", [])
        if isinstance(atype2, str):
            atype2 = [atype2]
        return type_name in atype2

    def _check_dataplant_compliance(self, errors: List) -> bool:
        """Check if ARC meets DataPLANT specification requirements."""
        # Check for critical DataPLANT requirements
        critical_errors = [
            e
            for e in errors
            if any(
                term in e
                for term in ["isa.investigation.xlsx", "ro-crate-metadata.json", "Investigation"]
            )
        ]
        return len(critical_errors) == 0

    def _check_fairagro_compliance(self, errors: List) -> bool:
        """Check if ARC meets FAIRagro requirements."""
        # Check for FAIRagro-specific errors
        fairagro_errors = [
            e
            for e in errors
            if any(
                term in e
                for term in ["Investigation", "Study", "Assay", "creator", "measurementTechnique"]
            )
        ]
        return len(fairagro_errors) == 0

    def _check_publishable_compliance(self, errors: List, warnings: List) -> bool:
        """Check if ARC meets publishable requirements."""
        # Check for publishable requirements
        publishable_errors = [
            e
            for e in errors
            if any(
                term in e
                for term in ["isa.investigation.xlsx", "Investigation", "identifier", "license"]
            )
        ]
        return len(publishable_errors) == 0

    def get_template_info(self) -> Dict:
        """Get template information."""
        return {
            "template_id": self.template["template_id"],
            "name": self.template["name"],
            "description": self.template["description"],
            "version": self.template["version"],
            "specification": self.template.get("specification", ""),
            "required_entities": self.template["required_entities"],
            "required_fields": self.template["required_fields"],
            "arc_structure": self.template.get("arc_structure", {}),
            "required_isa_files": self.template.get("required_isa_files", []),
        }
