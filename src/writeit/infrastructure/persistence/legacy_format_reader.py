"""Legacy format detection and reading infrastructure.

Provides utilities for detecting and reading legacy data formats from
pre-DDD versions of WriteIt, supporting smooth migration to the new
domain-driven architecture.
"""

import json
import yaml
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from pathlib import Path
from enum import Enum
import logging
from datetime import datetime

from ...domains.workspace.value_objects import WorkspaceName
from ...domains.content.value_objects import TemplateName, StyleName
from ...domains.pipeline.value_objects import PipelineId, StepId


class LegacyFormatType(str, Enum):
    """Types of legacy data formats."""
    # Configuration formats
    LEGACY_CONFIG_YAML = "legacy_config_yaml"        # Old config.yaml format
    LEGACY_CONFIG_JSON = "legacy_config_json"        # Old config.json format
    
    # Template formats
    LEGACY_TEMPLATE_YAML = "legacy_template_yaml"    # Old template.yaml format
    LEGACY_TEMPLATE_JSON = "legacy_template_json"    # Old template.json format
    
    # Style formats
    LEGACY_STYLE_YAML = "legacy_style_yaml"          # Old style.yaml format
    LEGACY_STYLE_JSON = "legacy_style_json"          # Old style.json format
    
    # Pipeline formats
    LEGACY_PIPELINE_YAML = "legacy_pipeline_yaml"    # Old pipeline.yaml format
    LEGACY_PIPELINE_JSON = "legacy_pipeline_json"    # Old pipeline.json format
    
    # Data storage formats
    LEGACY_LMDB_V1 = "legacy_lmdb_v1"                # LMDB format version 1
    LEGACY_LMDB_V2 = "legacy_lmdb_v2"                # LMDB format version 2
    LEGACY_PICKLE = "legacy_pickle"                  # Pickle serialized data
    
    # Workspace formats
    LEGACY_WORKSPACE_STRUCT = "legacy_workspace_struct"  # Old workspace directory structure
    LEGACY_DOT_WRITEIT = "legacy_dot_writeit"        # Old .writeit directory format


class FormatCompatibility(str, Enum):
    """Compatibility levels for legacy formats."""
    FULL_COMPATIBLE = "full_compatible"      # Fully compatible, direct migration
    PARTIAL_COMPATIBLE = "partial_compatible"  # Requires transformation
    MANUAL_MIGRATION = "manual_migration"      # Requires manual intervention
    INCOMPATIBLE = "incompatible"            # Cannot be migrated automatically


@dataclass
class LegacyFormatInfo:
    """Information about a detected legacy format."""
    format_type: LegacyFormatType
    file_path: Path
    detected_at: datetime
    version: Optional[str] = None
    size_bytes: Optional[int] = None
    compatibility: FormatCompatibility = FormatCompatibility.FULL_COMPATIBLE
    issues: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MigrationRequirements:
    """Requirements for migrating a legacy format."""
    source_format: LegacyFormatInfo
    target_format: str
    transformations_needed: List[str]
    data_loss_risk: str  # none, low, medium, high
    estimated_time_minutes: int
    prerequisites: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class DataMapping:
    """Mapping between legacy and new data structures."""
    legacy_path: str
    new_path: str
    transformation: Optional[str] = None  # None for direct mapping
    required: bool = True
    default_value: Any = None
    validation_rules: List[str] = None
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []


class LegacyFormatDetector(ABC):
    """Abstract base class for legacy format detectors."""
    
    @abstractmethod
    def can_detect(self, file_path: Path) -> bool:
        """Check if this detector can handle the given file."""
        pass
    
    @abstractmethod
    def detect_format(self, file_path: Path) -> Optional[LegacyFormatInfo]:
        """Detect the format of the given file."""
        pass


class LegacyFormatReader(ABC):
    """Abstract base class for legacy format readers."""
    
    @abstractmethod
    def can_read(self, format_type: LegacyFormatType) -> bool:
        """Check if this reader can handle the given format."""
        pass
    
    @abstractmethod
    def read_data(self, file_path: Path, format_info: LegacyFormatInfo) -> Dict[str, Any]:
        """Read data from the legacy format."""
        pass


class LegacyFormatTransformer(ABC):
    """Abstract base class for legacy format transformers."""
    
    @abstractmethod
    def can_transform(self, source_format: LegacyFormatType, target_format: str) -> bool:
        """Check if this transformer can handle the transformation."""
        pass
    
    @abstractmethod
    def transform_data(self, source_data: Dict[str, Any], mapping: DataMapping) -> Dict[str, Any]:
        """Transform data from legacy to new format."""
        pass
    
    @abstractmethod
    def get_migration_requirements(self, source_format: LegacyFormatType, target_format: str) -> MigrationRequirements:
        """Get requirements for the migration."""
        pass


class ConfigYamlDetector(LegacyFormatDetector):
    """Detector for legacy YAML configuration files."""
    
    def can_detect(self, file_path: Path) -> bool:
        return (file_path.name == "config.yaml" or 
                file_path.name == "config.yml") and file_path.exists()
    
    def detect_format(self, file_path: Path) -> Optional[LegacyFormatInfo]:
        if not self.can_detect(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Analyze the config structure to determine version
            version = self._detect_config_version(config_data)
            compatibility = self._assess_compatibility(config_data)
            issues = self._identify_issues(config_data)
            
            return LegacyFormatInfo(
                format_type=LegacyFormatType.LEGACY_CONFIG_YAML,
                file_path=file_path,
                detected_at=datetime.now(),
                version=version,
                size_bytes=file_path.stat().st_size,
                compatibility=compatibility,
                issues=issues,
                metadata={"keys_found": list(config_data.keys()) if config_data else []}
            )
            
        except Exception as e:
            return LegacyFormatInfo(
                format_type=LegacyFormatType.LEGACY_CONFIG_YAML,
                file_path=file_path,
                detected_at=datetime.now(),
                compatibility=FormatCompatibility.INCOMPATIBLE,
                issues=[f"Failed to read YAML: {str(e)}"]
            )
    
    def _detect_config_version(self, config_data: Dict[str, Any]) -> Optional[str]:
        """Detect the version of the legacy config format."""
        if not config_data:
            return "unknown"
        
        # Look for version indicators
        if "version" in config_data:
            return str(config_data["version"])
        
        # Look for structural indicators
        if "workspace" in config_data and "default_model" in config_data:
            return "1.0"
        elif "settings" in config_data:
            return "0.9"
        
        return "unknown"
    
    def _assess_compatibility(self, config_data: Dict[str, Any]) -> FormatCompatibility:
        """Assess compatibility with new configuration format."""
        if not config_data:
            return FormatCompatibility.INCOMPATIBLE
        
        # Check for incompatible keys or structures
        incompatible_keys = {"legacy_api_key", "deprecated_feature"}
        found_incompatible = any(key in config_data for key in incompatible_keys)
        
        if found_incompatible:
            return FormatCompatibility.INCOMPATIBLE
        
        # Check for keys that need transformation
        transform_keys = {"default_model", "workspace_settings"}
        needs_transform = any(key in config_data for key in transform_keys)
        
        if needs_transform:
            return FormatCompatibility.PARTIAL_COMPATIBLE
        
        return FormatCompatibility.FULL_COMPATIBLE
    
    def _identify_issues(self, config_data: Dict[str, Any]) -> List[str]:
        """Identify potential issues with the config."""
        issues = []
        
        if not config_data:
            issues.append("Empty configuration file")
            return issues
        
        # Check for deprecated settings
        deprecated_keys = {"old_api_endpoint", "legacy_cache_size"}
        for key in deprecated_keys:
            if key in config_data:
                issues.append(f"Deprecated setting found: {key}")
        
        # Check for missing required settings in new format
        required_new_keys = {"workspace", "defaults"}
        missing_keys = required_new_keys - set(config_data.keys())
        if missing_keys:
            issues.append(f"Missing settings for new format: {', '.join(missing_keys)}")
        
        return issues


class TemplateYamlDetector(LegacyFormatDetector):
    """Detector for legacy YAML template files."""
    
    def can_detect(self, file_path: Path) -> bool:
        return (file_path.suffix in ['.yaml', '.yml'] and 
                'template' in file_path.name.lower() and 
                file_path.exists())
    
    def detect_format(self, file_path: Path) -> Optional[LegacyFormatInfo]:
        if not self.can_detect(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                template_data = yaml.safe_load(f)
            
            # Analyze template structure
            version = self._detect_template_version(template_data)
            compatibility = self._assess_compatibility(template_data)
            issues = self._identify_issues(template_data)
            
            return LegacyFormatInfo(
                format_type=LegacyFormatType.LEGACY_TEMPLATE_YAML,
                file_path=file_path,
                detected_at=datetime.now(),
                version=version,
                size_bytes=file_path.stat().st_size,
                compatibility=compatibility,
                issues=issues,
                metadata={
                    "template_type": template_data.get("type", "unknown"),
                    "steps_count": len(template_data.get("steps", [])),
                }
            )
            
        except Exception as e:
            return LegacyFormatInfo(
                format_type=LegacyFormatType.LEGACY_TEMPLATE_YAML,
                file_path=file_path,
                detected_at=datetime.now(),
                compatibility=FormatCompatibility.INCOMPATIBLE,
                issues=[f"Failed to read template YAML: {str(e)}"]
            )
    
    def _detect_template_version(self, template_data: Dict[str, Any]) -> Optional[str]:
        """Detect the version of the legacy template format."""
        if not template_data:
            return "unknown"
        
        if "version" in template_data:
            return str(template_data["version"])
        
        # Look for structural indicators
        if "metadata" in template_data and "steps" in template_data:
            return "2.0"
        elif "name" in template_data and "prompt" in template_data:
            return "1.0"
        
        return "unknown"
    
    def _assess_compatibility(self, template_data: Dict[str, Any]) -> FormatCompatibility:
        """Assess compatibility with new template format."""
        if not template_data:
            return FormatCompatibility.INCOMPATIBLE
        
        # Check for new format structure
        required_sections = {"metadata", "steps", "inputs"}
        has_new_structure = all(section in template_data for section in required_sections)
        
        if has_new_structure:
            return FormatCompatibility.FULL_COMPATIBLE
        
        # Check for transformable structure
        transformable_sections = {"name", "prompt", "steps"}
        has_transformable = any(section in template_data for section in transformable_sections)
        
        if has_transformable:
            return FormatCompatibility.PARTIAL_COMPATIBLE
        
        return FormatCompatibility.INCOMPATIBLE
    
    def _identify_issues(self, template_data: Dict[str, Any]) -> List[str]:
        """Identify potential issues with the template."""
        issues = []
        
        if not template_data:
            issues.append("Empty template file")
            return issues
        
        # Check for deprecated fields
        deprecated_fields = {"old_prompt_format", "legacy_model"}
        for field in deprecated_fields:
            if field in template_data:
                issues.append(f"Deprecated field found: {field}")
        
        # Check for required fields in new format
        required_fields = {"metadata", "steps"}
        missing_fields = required_fields - set(template_data.keys())
        if missing_fields:
            issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        return issues


class LegacyFormatReaderImpl(LegacyFormatReader):
    """Implementation of legacy format reader."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def can_read(self, format_type: LegacyFormatType) -> bool:
        # This reader can handle all basic formats
        return True
    
    def read_data(self, file_path: Path, format_info: LegacyFormatInfo) -> Dict[str, Any]:
        """Read data from the legacy format."""
        try:
            if format_type.format_type in [LegacyFormatType.LEGACY_CONFIG_YAML, 
                                         LegacyFormatType.LEGACY_TEMPLATE_YAML,
                                         LegacyFormatType.LEGACY_STYLE_YAML,
                                         LegacyFormatType.LEGACY_PIPELINE_YAML]:
                return self._read_yaml_file(file_path)
            
            elif format_type.format_type in [LegacyFormatType.LEGACY_CONFIG_JSON,
                                             LegacyFormatType.LEGACY_TEMPLATE_JSON,
                                             LegacyFormatType.LEGACY_STYLE_JSON,
                                             LegacyFormatType.LEGACY_PIPELINE_JSON]:
                return self._read_json_file(file_path)
            
            elif format_type.format_type == LegacyFormatType.LEGACY_PICKLE:
                return self._read_pickle_file(file_path)
            
            else:
                raise ValueError(f"Unsupported format type: {format_type.format_type}")
                
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            raise
    
    def _read_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Read YAML file."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f) or {}
    
    def _read_pickle_file(self, file_path: Path) -> Dict[str, Any]:
        """Read pickle file (with security warning)."""
        # Security warning: pickle can be unsafe
        self.logger.warning(f"Reading pickle file {file_path} - ensure file is trusted")
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        # Ensure data is dict-like
        if not isinstance(data, dict):
            return {"_raw_data": data}
        
        return data


class LegacyFormatTransformerImpl(LegacyFormatTransformer):
    """Implementation of legacy format transformer."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._mappings = self._initialize_mappings()
    
    def can_transform(self, source_format: LegacyFormatType, target_format: str) -> bool:
        """Check if this transformer can handle the transformation."""
        return (source_format, target_format) in self._mappings
    
    def transform_data(self, source_data: Dict[str, Any], mapping: DataMapping) -> Dict[str, Any]:
        """Transform data from legacy to new format."""
        try:
            # Extract value from source data
            source_value = self._get_nested_value(source_data, mapping.legacy_path)
            
            # Apply transformation if specified
            if mapping.transformation:
                source_value = self._apply_transformation(source_value, mapping.transformation)
            
            # Use default value if source value is None and default is provided
            if source_value is None and mapping.default_value is not None:
                source_value = mapping.default_value
            
            # Apply validation rules
            if mapping.validation_rules:
                source_value = self._apply_validation(source_value, mapping.validation_rules)
            
            # Set value in target data
            target_data = {}
            self._set_nested_value(target_data, mapping.new_path, source_value)
            
            return target_data
            
        except Exception as e:
            self.logger.error(f"Error transforming {mapping.legacy_path} to {mapping.new_path}: {e}")
            if mapping.required:
                raise
            return {}
    
    def get_migration_requirements(self, source_format: LegacyFormatType, target_format: str) -> MigrationRequirements:
        """Get requirements for the migration."""
        source_info = LegacyFormatInfo(
            format_type=source_format,
            file_path=Path("dummy"),
            detected_at=datetime.now()
        )
        
        # Basic requirements based on format type
        requirements = {
            (LegacyFormatType.LEGACY_CONFIG_YAML, "workspace_config"): MigrationRequirements(
                source_format=source_info,
                target_format="workspace_config",
                transformations_needed=["map_settings", "convert_workspace_structure"],
                data_loss_risk="low",
                estimated_time_minutes=5,
                prerequisites=["valid_yaml"],
                warnings=["Review workspace-specific settings after migration"]
            ),
            
            (LegacyFormatType.LEGACY_TEMPLATE_YAML, "pipeline_template"): MigrationRequirements(
                source_format=source_info,
                target_format="pipeline_template",
                transformations_needed=["add_metadata", "restructure_steps", "convert_inputs"],
                data_loss_risk="medium",
                estimated_time_minutes=15,
                prerequisites=["valid_yaml", "compatible_step_structure"],
                warnings=["Review pipeline configuration after migration", "Test migrated pipelines"]
            ),
        }
        
        return requirements.get((source_format, target_format), MigrationRequirements(
            source_format=source_info,
            target_format=target_format,
            transformations_needed=["generic_conversion"],
            data_loss_risk="unknown",
            estimated_time_minutes=30,
            prerequisites=["file_readable"],
            warnings=["Unknown migration path - manual review required"]
        ))
    
    def _initialize_mappings(self) -> Dict[Tuple[LegacyFormatType, str], List[DataMapping]]:
        """Initialize data mappings for known transformations."""
        return {
            (LegacyFormatType.LEGACY_CONFIG_YAML, "workspace_config"): [
                DataMapping(
                    legacy_path="default_model",
                    new_path="defaults.model",
                    transformation="rename_model_preference"
                ),
                DataMapping(
                    legacy_path="workspace",
                    new_path="workspace.name",
                    transformation="extract_workspace_name"
                ),
                DataMapping(
                    legacy_path="cache_size",
                    new_path="cache.max_size",
                    transformation="convert_size_units"
                ),
            ],
            
            (LegacyFormatType.LEGACY_TEMPLATE_YAML, "pipeline_template"): [
                DataMapping(
                    legacy_path="name",
                    new_path="metadata.name",
                    required=True
                ),
                DataMapping(
                    legacy_path="description",
                    new_path="metadata.description",
                    default_value=""
                ),
                DataMapping(
                    legacy_path="steps",
                    new_path="steps",
                    transformation="convert_step_structure"
                ),
            ],
        }
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from data using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested value in data using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to value."""
        # Placeholder for transformation logic
        # In a real implementation, this would have specific transformation functions
        return value
    
    def _apply_validation(self, value: Any, rules: List[str]) -> Any:
        """Apply validation rules to value."""
        # Placeholder for validation logic
        # In a real implementation, this would validate the value
        return value


class LegacyFormatManager:
    """Manager for legacy format detection, reading, and transformation."""
    
    def __init__(self):
        self.detectors: List[LegacyFormatDetector] = []
        self.reader: LegacyFormatReader = LegacyFormatReaderImpl()
        self.transformer: LegacyFormatTransformer = LegacyFormatTransformerImpl()
        self.logger = logging.getLogger(__name__)
        
        # Register default detectors
        self._register_default_detectors()
    
    def register_detector(self, detector: LegacyFormatDetector) -> None:
        """Register a legacy format detector."""
        self.detectors.append(detector)
    
    def detect_legacy_formats(self, search_path: Path) -> List[LegacyFormatInfo]:
        """Detect all legacy formats in the given path."""
        detected_formats = []
        
        if not search_path.exists():
            self.logger.warning(f"Search path does not exist: {search_path}")
            return detected_formats
        
        # Search for files
        files_to_check = []
        if search_path.is_file():
            files_to_check = [search_path]
        elif search_path.is_dir():
            files_to_check = list(search_path.rglob("*"))
        
        # Check each file with registered detectors
        for file_path in files_to_check:
            if file_path.is_file():
                for detector in self.detectors:
                    try:
                        format_info = detector.detect_format(file_path)
                        if format_info:
                            detected_formats.append(format_info)
                            break  # Stop after first successful detection
                    except Exception as e:
                        self.logger.warning(f"Error detecting format for {file_path}: {e}")
        
        self.logger.info(f"Detected {len(detected_formats)} legacy formats in {search_path}")
        return detected_formats
    
    def read_legacy_data(self, format_info: LegacyFormatInfo) -> Dict[str, Any]:
        """Read data from a legacy format."""
        try:
            return self.reader.read_data(format_info.file_path, format_info)
        except Exception as e:
            self.logger.error(f"Error reading legacy data from {format_info.file_path}: {e}")
            raise
    
    def get_migration_plan(self, format_info: LegacyFormatInfo, target_format: str) -> MigrationRequirements:
        """Get migration requirements for a format."""
        return self.transformer.get_migration_requirements(format_info.format_type, target_format)
    
    def transform_legacy_data(self, source_data: Dict[str, Any], format_info: LegacyFormatInfo, 
                             target_format: str) -> Dict[str, Any]:
        """Transform legacy data to new format."""
        if not self.transformer.can_transform(format_info.format_type, target_format):
            raise ValueError(f"Cannot transform {format_info.format_type} to {target_format}")
        
        # Get mappings for this transformation
        mappings = self.transformer._mappings.get((format_info.format_type, target_format), [])
        
        # Apply each mapping
        target_data = {}
        for mapping in mappings:
            try:
                transformed = self.transformer.transform_data(source_data, mapping)
                # Merge transformed data
                self._merge_dicts(target_data, transformed)
            except Exception as e:
                if mapping.required:
                    self.logger.error(f"Required transformation failed: {mapping.legacy_path} -> {mapping.new_path}")
                    raise
                self.logger.warning(f"Optional transformation failed: {mapping.legacy_path} -> {mapping.new_path}: {e}")
        
        return target_data
    
    def _register_default_detectors(self) -> None:
        """Register default format detectors."""
        self.register_detector(ConfigYamlDetector())
        self.register_detector(TemplateYamlDetector())
    
    def _merge_dicts(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dicts(target[key], value)
            else:
                target[key] = value