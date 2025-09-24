"""Legacy Format Converter for WriteIt Data Migration.

This module handles conversion of specific legacy formats to the new DDD structure.
It includes converters for:
- Legacy YAML pipeline templates to DDD PipelineTemplate objects
- Old workspace configurations to new structure
- Legacy LMDB data formats to new schema
- Cache format updates
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import uuid

from writeit.domains.pipeline.entities import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.value_objects import (
    PipelineId, StepId, PromptTemplate, ModelPreference
)


class LegacyFormatConverter:
    """Converts legacy formats to DDD structure."""
    
    def __init__(self):
        self.conversion_log = []
        
    def log_conversion(self, message: str, level: str = "info") -> None:
        """Log conversion activity."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.conversion_log.append(log_entry)
        
    def convert_pipeline_template_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Convert legacy YAML pipeline template to new format.
        
        Args:
            yaml_content: Legacy YAML template content
            
        Returns:
            Converted template data ready for DDD PipelineTemplate creation
        """
        try:
            # Parse legacy YAML
            legacy_data = yaml.safe_load(yaml_content)
            if not legacy_data:
                raise ValueError("Empty YAML content")
                
            converted = {
                "metadata": self._convert_metadata(legacy_data.get("metadata", {})),
                "inputs": self._convert_inputs(legacy_data.get("inputs", {})),
                "steps": self._convert_steps(legacy_data.get("steps", [])),
                "defaults": legacy_data.get("defaults", {}),
                "tags": legacy_data.get("tags", []),
                "author": legacy_data.get("author"),
                "version": legacy_data.get("version", "1.0.0")
            }
            
            self.log_conversion(f"Converted pipeline template with {len(converted['steps'])} steps")
            return converted
            
        except Exception as e:
            self.log_conversion(f"Failed to convert pipeline template: {e}", "error")
            raise ValueError(f"Template conversion failed: {e}")
            
    def _convert_metadata(self, legacy_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy metadata to new format."""
        converted = {
            "name": legacy_metadata.get("name", "Untitled Pipeline"),
            "description": legacy_metadata.get("description", ""),
            "created_at": legacy_metadata.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "converted_at": datetime.now().isoformat()
        }
        
        # Add conversion metadata
        converted["_conversion_info"] = {
            "from_version": legacy_metadata.get("version", "1.0.0"),
            "converted_at": datetime.now().isoformat(),
            "converter_version": "1.0"
        }
        
        return converted
        
    def _convert_inputs(self, legacy_inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert legacy input definitions to new format."""
        converted = []
        
        for key, config in legacy_inputs.items():
            # Handle different legacy formats
            if isinstance(config, dict):
                # New format
                input_def = {
                    "key": key,
                    "type": config.get("type", "text"),
                    "label": config.get("label", key.title()),
                    "required": config.get("required", False),
                    "default": config.get("default"),
                    "placeholder": config.get("placeholder", ""),
                    "help": config.get("help", ""),
                    "max_length": config.get("max_length"),
                    "validation": config.get("validation", {})
                }
                
                # Handle choice options
                if config.get("type") == "choice" and "options" in config:
                    options = config["options"]
                    if isinstance(options, list):
                        input_def["options"] = [
                            {"label": opt, "value": opt} if isinstance(opt, str) else opt
                            for opt in options
                        ]
                    else:
                        input_def["options"] = []
                        
            else:
                # Old format (just type)
                input_def = {
                    "key": key,
                    "type": str(config),
                    "label": key.title(),
                    "required": False,
                    "default": None,
                    "placeholder": "",
                    "help": "",
                    "validation": {}
                }
                
            converted.append(input_def)
            
        return converted
        
    def _convert_steps(self, legacy_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert legacy step definitions to new format."""
        converted = []
        
        for step_data in legacy_steps:
            if not isinstance(step_data, dict):
                continue
                
            # Handle both old and new step formats
            step_def = {
                "name": step_data.get("name", "Unnamed Step"),
                "description": step_data.get("description", ""),
                "type": step_data.get("type", "llm_generate"),
                "key": step_data.get("key", step_data.get("name", "step").lower().replace(" ", "_")),
                "prompt_template": step_data.get("prompt_template", ""),
                "selection_prompt": step_data.get("selection_prompt", ""),
                "model_preference": self._convert_model_preference(step_data.get("model_preference", ["gpt-4o-mini"])),
                "depends_on": step_data.get("depends_on", []),
                "parallel": step_data.get("parallel", False),
                "validation": step_data.get("validation", {}),
                "ui": step_data.get("ui", {}),
                "retry_config": step_data.get("retry_config", {})
            }
            
            converted.append(step_def)
            
        return converted
        
    def _convert_model_preference(self, preference: Union[str, List[str]]) -> List[str]:
        """Convert model preference to consistent format."""
        if isinstance(preference, str):
            return [preference]
        elif isinstance(preference, list):
            return [str(p) for p in preference]
        else:
            return ["gpt-4o-mini"]
            
    def convert_workspace_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy workspace configuration to new format.
        
        Args:
            legacy_config: Legacy configuration dictionary
            
        Returns:
            Converted configuration dictionary
        """
        converted = {
            "version": "2.0.0",
            "workspace_name": legacy_config.get("name", "default"),
            "created_at": legacy_config.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "settings": {
                "default_model": legacy_config.get("default_model", "gpt-4o-mini"),
                "auto_save": legacy_config.get("auto_save", True),
                "max_history": legacy_config.get("max_history", 1000),
                "ui_theme": legacy_config.get("ui_theme", "default"),
                "debug_mode": legacy_config.get("debug_mode", False)
            },
            "llm_providers": legacy_config.get("llm_providers", {}),
            "metadata": {
                "converted_at": datetime.now().isoformat(),
                "from_version": legacy_config.get("writeit_version", "0.1.0"),
                "migration_notes": "Converted from legacy format to DDD structure"
            }
        }
        
        self.log_conversion(f"Converted workspace config for {converted['workspace_name']}")
        return converted
        
    def convert_lmdb_entry(self, key: bytes, value: bytes) -> Dict[str, Any]:
        """Convert legacy LMDB entry to new format.
        
        Args:
            key: Entry key
            value: Entry value
            
        Returns:
            Converted entry data
        """
        try:
            # Try to decode as JSON first
            try:
                entry_data = json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Binary data, return as-is with metadata
                return {
                    "_converted": True,
                    "_converted_at": datetime.now().isoformat(),
                    "_data_type": "binary",
                    "_key": key.decode('utf-8', errors='ignore'),
                    "value": value.hex()
                }
                
            # Convert entry data
            converted = {
                "_converted": True,
                "_converted_at": datetime.now().isoformat(),
                "_key": key.decode('utf-8', errors='ignore'),
                "_original_data": entry_data
            }
            
            # Handle specific entry types
            if "pipeline_run" in entry_data:
                converted["pipeline_run"] = self._convert_pipeline_run(entry_data["pipeline_run"])
            elif "cache" in entry_data:
                converted["cache"] = self._convert_cache_entry(entry_data["cache"])
            else:
                converted["data"] = entry_data
                
            return converted
            
        except Exception as e:
            self.log_conversion(f"Failed to convert LMDB entry {key}: {e}", "error")
            return {
                "_converted": False,
                "_error": str(e),
                "_key": key.decode('utf-8', errors='ignore'),
                "_converted_at": datetime.now().isoformat()
            }
            
    def _convert_pipeline_run(self, legacy_run: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy pipeline run data to new format."""
        converted = legacy_run.copy()
        
        # Add DDD-specific fields
        converted["domain_id"] = converted.get("id", str(uuid.uuid4()))
        converted["workspace_isolated"] = True
        converted["migration_version"] = "2.0.0"
        converted["migrated_at"] = datetime.now().isoformat()
        
        # Convert step executions if present
        if "step_executions" in converted:
            converted["step_executions"] = [
                self._convert_step_execution(step) 
                for step in converted["step_executions"]
            ]
            
        return converted
        
    def _convert_step_execution(self, legacy_step: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy step execution data to new format."""
        converted = legacy_step.copy()
        
        # Add DDD-specific fields
        converted["step_id"] = converted.get("step_key", converted.get("id", "unknown"))
        converted["domain_compatible"] = True
        converted["migration_version"] = "2.0.0"
        converted["migrated_at"] = datetime.now().isoformat()
        
        return converted
        
    def _convert_cache_entry(self, legacy_cache: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy cache entry to new format."""
        converted = legacy_cache.copy()
        
        # Add DDD-specific cache fields
        converted["workspace_isolated"] = True
        converted["cache_version"] = "2.0"
        converted["migration_version"] = "2.0.0"
        converted["migrated_at"] = datetime.now().isoformat()
        
        # Convert metadata
        if "metadata" in converted:
            if isinstance(converted["metadata"], dict):
                converted["metadata"]["converted"] = True
                converted["metadata"]["converted_at"] = datetime.now().isoformat()
                
        return converted
        
    def convert_template_file(self, template_path: Path) -> PipelineTemplate:
        """Convert a legacy template file to DDD PipelineTemplate.
        
        Args:
            template_path: Path to legacy template file
            
        Returns:
            Converted PipelineTemplate object
        """
        try:
            # Read template file
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Convert YAML to DDD structure
            converted_data = self.convert_pipeline_template_yaml(content)
            
            # Create DDD PipelineTemplate
            pipeline_id = PipelineId.from_name(converted_data["metadata"]["name"])
            
            # Convert inputs
            inputs = []
            for input_data in converted_data["inputs"]:
                inputs.append(PipelineInput(
                    key=input_data["key"],
                    type=input_data["type"],
                    label=input_data["label"],
                    required=input_data["required"],
                    default=input_data["default"],
                    placeholder=input_data["placeholder"],
                    help=input_data["help"],
                    max_length=input_data["max_length"],
                    validation=input_data["validation"],
                    options=input_data.get("options", [])
                ))
                
            # Convert steps
            steps = []
            for step_data in converted_data["steps"]:
                step_id = StepId(step_data["key"])
                prompt_template = PromptTemplate(step_data["prompt_template"])
                model_preference = ModelPreference(step_data["model_preference"])
                depends_on = [StepId(dep) for dep in step_data["depends_on"]]
                
                steps.append(PipelineStepTemplate(
                    id=step_id,
                    name=step_data["name"],
                    description=step_data["description"],
                    type=step_data["type"],
                    prompt_template=prompt_template,
                    selection_prompt=step_data["selection_prompt"],
                    model_preference=model_preference,
                    validation=step_data["validation"],
                    ui=step_data["ui"],
                    depends_on=depends_on,
                    parallel=step_data["parallel"],
                    retry_config=step_data["retry_config"]
                ))
                
            # Create PipelineTemplate
            template = PipelineTemplate.create(
                name=converted_data["metadata"]["name"],
                description=converted_data["metadata"]["description"],
                inputs=inputs,
                steps=steps,
                version=converted_data["version"],
                metadata=converted_data["metadata"],
                defaults=converted_data["defaults"],
                tags=converted_data["tags"],
                author=converted_data["author"]
            )
            
            self.log_conversion(f"Successfully converted template: {template.name}")
            return template
            
        except Exception as e:
            self.log_conversion(f"Failed to convert template file {template_path}: {e}", "error")
            raise ValueError(f"Template file conversion failed: {e}")
            
    def get_conversion_log(self) -> List[Dict[str, Any]]:
        """Get conversion log.
        
        Returns:
            List of conversion log entries
        """
        return self.conversion_log
        
    def generate_conversion_report(self) -> str:
        """Generate a detailed conversion report.
        
        Returns:
            Formatted conversion report
        """
        log = self.get_conversion_log()
        
        report = [
            "# Legacy Format Conversion Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Conversion Summary",
            f"Total conversions: {len(log)}",
            "",
            "## Conversion Log",
            ""
        ]
        
        # Group by level
        by_level = {'info': [], 'error': []}
        for entry in log:
            level = entry.get('level', 'info')
            by_level[level].append(entry)
            
        # Add errors
        if by_level['error']:
            report.append("### Errors")
            for entry in by_level['error']:
                report.append(f"- {entry['timestamp']}: {entry['message']}")
            report.append("")
            
        # Add info
        if by_level['info']:
            report.append("### Successful Conversions")
            for entry in by_level['info']:
                report.append(f"- {entry['timestamp']}: {entry['message']}")
            report.append("")
            
        return "\n".join(report)