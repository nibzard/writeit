"""
Template documentation extractor from YAML files
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models import (
    TemplateDocumentationSet,
    TemplateDocumentation,
    TemplateFieldDocumentation,
    TemplateStepDocumentation
)


class TemplateExtractor:
    """Extract template documentation from YAML files"""
    
    def extract_templates(self, template_path: Path) -> TemplateDocumentationSet:
        """Extract complete template documentation"""
        template_set = TemplateDocumentationSet(templates=[], style_primers=[])
        
        # Extract pipeline templates
        pipeline_dir = template_path / "pipelines"
        if pipeline_dir.exists():
            for template_file in pipeline_dir.glob("*.yaml"):
                template_doc = self._extract_pipeline_template(template_file)
                if template_doc:
                    template_set.templates.append(template_doc)
        
        # Extract style primers
        styles_dir = template_path / "styles"
        if styles_dir.exists():
            for style_file in styles_dir.glob("*.yaml"):
                style_doc = self._extract_style_primer(style_file)
                if style_doc:
                    template_set.style_primers.append(style_doc)
        
        return template_set
    
    def _extract_pipeline_template(self, template_file: Path) -> Optional[TemplateDocumentation]:
        """Extract documentation for a pipeline template"""
        try:
            with open(template_file, 'r') as f:
                template_data = yaml.safe_load(f)
            
            template_doc = TemplateDocumentation(
                name=template_data.get("metadata", {}).get("name", template_file.stem),
                description=template_data.get("metadata", {}).get("description", ""),
                version=template_data.get("metadata", {}).get("version", "1.0.0"),
                metadata=template_data.get("metadata", {}),
                inputs=[],
                defaults=template_data.get("defaults", {}),
                steps=[],
                examples=self._extract_template_examples(template_data),
                source_file=template_file
            )
            
            # Extract inputs
            inputs = template_data.get("inputs", {})
            for input_name, input_data in inputs.items():
                input_doc = self._extract_input_field(input_name, input_data)
                template_doc.inputs.append(input_doc)
            
            # Extract steps
            steps = template_data.get("steps", {})
            for step_key, step_data in steps.items():
                step_doc = self._extract_step(step_key, step_data)
                template_doc.steps.append(step_doc)
            
            return template_doc
        
        except Exception as e:
            print(f"Error extracting template docs from {template_file}: {e}")
            return None
    
    def _extract_style_primer(self, style_file: Path) -> Optional[TemplateDocumentation]:
        """Extract documentation for a style primer"""
        try:
            with open(style_file, 'r') as f:
                style_data = yaml.safe_load(f)
            
            style_doc = TemplateDocumentation(
                name=style_data.get("name", style_file.stem),
                description=style_data.get("description", ""),
                version=style_data.get("version", "1.0.0"),
                metadata=style_data,
                inputs=[],
                defaults={},
                steps=[],
                examples=self._extract_style_examples(style_data),
                source_file=style_file
            )
            
            return style_doc
        
        except Exception as e:
            print(f"Error extracting style docs from {style_file}: {e}")
            return None
    
    def _extract_input_field(self, name: str, input_data: Dict[str, Any]) -> TemplateFieldDocumentation:
        """Extract documentation for an input field"""
        field_doc = TemplateFieldDocumentation(
            name=name,
            type=input_data.get("type", "text"),
            description=input_data.get("description", ""),
            required=input_data.get("required", False),
            default_value=input_data.get("default"),
            options=input_data.get("options"),
            validation=input_data.get("validation")
        )
        
        # Extract help text if available
        if "help" in input_data:
            field_doc.description += f"\n\nHelp: {input_data['help']}"
        
        # Extract placeholder text
        if "placeholder" in input_data:
            field_doc.description += f"\n\nPlaceholder: {input_data['placeholder']}"
        
        return field_doc
    
    def _extract_step(self, key: str, step_data: Dict[str, Any]) -> TemplateStepDocumentation:
        """Extract documentation for a pipeline step"""
        step_doc = TemplateStepDocumentation(
            key=key,
            name=step_data.get("name", key),
            description=step_data.get("description", ""),
            type=step_data.get("type", "llm_generate"),
            parameters=step_data.get("parameters", {}),
            depends_on=step_data.get("depends_on", []),
            examples=self._extract_step_examples(step_data)
        )
        
        return step_doc
    
    def _extract_template_examples(self, template_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract examples from template data"""
        examples = []
        
        # Look for examples in the template
        if "examples" in template_data:
            examples.extend(template_data["examples"])
        
        # Generate example usage
        example_usage = {
            "description": f"Example usage of {template_data.get('metadata', {}).get('name', 'this template')}",
            "inputs": {},
            "steps": {}
        }
        
        # Generate sample inputs
        inputs = template_data.get("inputs", {})
        for input_name, input_data in inputs.items():
            if input_data.get("default"):
                example_usage["inputs"][input_name] = input_data["default"]
            elif input_data.get("type") == "choice" and input_data.get("options"):
                example_usage["inputs"][input_name] = input_data["options"][0]["value"]
            elif input_data.get("type") == "boolean":
                example_usage["inputs"][input_name] = True
            else:
                example_usage["inputs"][input_name] = f"sample_{input_name}"
        
        examples.append(example_usage)
        
        return examples
    
    def _extract_style_examples(self, style_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract examples from style primer data"""
        examples = []
        
        # Look for examples in the style primer
        if "examples" in style_data:
            examples.extend(style_data["examples"])
        
        # Generate example usage
        example_usage = {
            "description": f"Example usage of {style_data.get('name', 'this style')}",
            "application": "Apply this style to technical articles for developer audiences",
            "voice_characteristics": style_data.get("voice", {}).get("characteristics", []),
            "language_preferences": style_data.get("language", {}).get("preferences", [])
        }
        
        examples.append(example_usage)
        
        return examples
    
    def _extract_step_examples(self, step_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract examples from step data"""
        examples = []
        
        # Look for examples in the step
        if "examples" in step_data:
            examples.extend(step_data["examples"])
        
        # Generate example based on step type
        step_type = step_data.get("type", "llm_generate")
        if step_type == "llm_generate":
            example = {
                "description": f"Example {step_data.get('name', 'LLM generation')} step",
                "prompt_template": step_data.get("prompt_template", "Generate content about {{ inputs.topic }}"),
                "model_preference": step_data.get("model_preference", ["gpt-4o-mini"])
            }
            examples.append(example)
        
        return examples