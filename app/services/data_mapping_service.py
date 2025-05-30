from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
from app.schemas.ehr_sync import EHRSystem, FHIRResourceType
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataMappingService:
    def __init__(self):
        self.mapping_configs = self._load_mapping_configs()
        self.validation_rules = self._load_validation_rules()

    def _load_mapping_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load mapping configurations from settings."""
        return {
            "my_health_record": {
                "patient": {
                    "id": "identifier[0].value",
                    "name": "name[0].text",
                    "dob": "birthDate",
                    "gender": "gender"
                },
                "condition": {
                    "code": "code.coding[0].code",
                    "display": "code.coding[0].display",
                    "onset": "onsetDateTime",
                    "severity": "severity.coding[0].code"
                },
                "medication": {
                    "code": "medicationCodeableConcept.coding[0].code",
                    "display": "medicationCodeableConcept.coding[0].display",
                    "dosage": "dosage[0].text",
                    "status": "status"
                }
            },
            "epic": {
                # Epic specific mappings
            },
            "cerner": {
                # Cerner specific mappings
            }
        }

    def _load_validation_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load validation rules for different data types."""
        return {
            "patient": [
                {"field": "id", "required": True, "type": "string"},
                {"field": "name", "required": True, "type": "string"},
                {"field": "dob", "required": True, "type": "date"},
                {"field": "gender", "required": True, "type": "string", "enum": ["male", "female", "other", "unknown"]}
            ],
            "condition": [
                {"field": "code", "required": True, "type": "string"},
                {"field": "display", "required": True, "type": "string"},
                {"field": "onset", "required": True, "type": "datetime"},
                {"field": "severity", "required": False, "type": "string"}
            ],
            "medication": [
                {"field": "code", "required": True, "type": "string"},
                {"field": "display", "required": True, "type": "string"},
                {"field": "dosage", "required": True, "type": "string"},
                {"field": "status", "required": True, "type": "string"}
            ]
        }

    def map_resource(
        self,
        source_system: EHRSystem,
        resource_type: FHIRResourceType,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map a resource from source system format to our standard format."""
        try:
            mapping_config = self.mapping_configs.get(source_system.value, {}).get(resource_type.value, {})
            if not mapping_config:
                raise ValueError(f"No mapping configuration found for {source_system} {resource_type}")

            mapped_data = {}
            for target_field, source_path in mapping_config.items():
                value = self._get_nested_value(data, source_path)
                mapped_data[target_field] = value

            # Validate mapped data
            self._validate_data(resource_type.value, mapped_data)

            return mapped_data
        except Exception as e:
            logger.error(f"Failed to map resource: {str(e)}")
            raise

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a value from nested dictionary using dot notation path."""
        try:
            parts = path.split('.')
            value = data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    value = value[int(part)]
                else:
                    return None
            return value
        except Exception:
            return None

    def _validate_data(self, resource_type: str, data: Dict[str, Any]) -> None:
        """Validate mapped data against validation rules."""
        rules = self.validation_rules.get(resource_type, [])
        for rule in rules:
            field = rule["field"]
            value = data.get(field)

            # Check required fields
            if rule["required"] and value is None:
                raise ValueError(f"Required field {field} is missing")

            # Check field type
            if value is not None:
                if rule["type"] == "string" and not isinstance(value, str):
                    raise ValueError(f"Field {field} must be a string")
                elif rule["type"] == "date" and not isinstance(value, (str, datetime)):
                    raise ValueError(f"Field {field} must be a date")
                elif rule["type"] == "datetime" and not isinstance(value, (str, datetime)):
                    raise ValueError(f"Field {field} must be a datetime")

            # Check enum values
            if "enum" in rule and value not in rule["enum"]:
                raise ValueError(f"Field {field} must be one of {rule['enum']}")

    def reconcile_data(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
        resource_type: FHIRResourceType
    ) -> Dict[str, Any]:
        """Reconcile data between local and remote sources."""
        try:
            reconciled_data = local_data.copy()

            # Compare timestamps
            local_timestamp = local_data.get("last_updated")
            remote_timestamp = remote_data.get("last_updated")

            if remote_timestamp and (not local_timestamp or remote_timestamp > local_timestamp):
                # Remote data is newer, update local data
                reconciled_data.update(remote_data)
                reconciled_data["source"] = "remote"
            else:
                # Local data is newer or same, keep local data
                reconciled_data["source"] = "local"

            # Handle conflicts
            if self._has_conflicts(local_data, remote_data):
                reconciled_data["conflicts"] = self._resolve_conflicts(
                    local_data,
                    remote_data,
                    resource_type
                )

            return reconciled_data
        except Exception as e:
            logger.error(f"Failed to reconcile data: {str(e)}")
            raise

    def _has_conflicts(self, local_data: Dict[str, Any], remote_data: Dict[str, Any]) -> bool:
        """Check if there are conflicts between local and remote data."""
        try:
            for key in set(local_data.keys()) & set(remote_data.keys()):
                if local_data[key] != remote_data[key]:
                    return True
            return False
        except Exception:
            return False

    def _resolve_conflicts(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
        resource_type: FHIRResourceType
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts between local and remote data."""
        conflicts = []
        for key in set(local_data.keys()) & set(remote_data.keys()):
            if local_data[key] != remote_data[key]:
                conflicts.append({
                    "field": key,
                    "local_value": local_data[key],
                    "remote_value": remote_data[key],
                    "resolution": "manual"  # Requires manual resolution
                })
        return conflicts

    def transform_to_fhir(
        self,
        data: Dict[str, Any],
        resource_type: FHIRResourceType
    ) -> Dict[str, Any]:
        """Transform data to FHIR format."""
        try:
            if resource_type == FHIRResourceType.PATIENT:
                return {
                    "resourceType": "Patient",
                    "identifier": [{"value": data["id"]}],
                    "name": [{"text": data["name"]}],
                    "birthDate": data["dob"],
                    "gender": data["gender"]
                }
            elif resource_type == FHIRResourceType.CONDITION:
                return {
                    "resourceType": "Condition",
                    "code": {
                        "coding": [{
                            "code": data["code"],
                            "display": data["display"]
                        }]
                    },
                    "onsetDateTime": data["onset"],
                    "severity": {
                        "coding": [{
                            "code": data["severity"]
                        }]
                    } if data.get("severity") else None
                }
            elif resource_type == FHIRResourceType.MEDICATION:
                return {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {
                        "coding": [{
                            "code": data["code"],
                            "display": data["display"]
                        }]
                    },
                    "dosage": [{
                        "text": data["dosage"]
                    }],
                    "status": data["status"]
                }
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
        except Exception as e:
            logger.error(f"Failed to transform to FHIR: {str(e)}")
            raise 