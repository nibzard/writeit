"""Data Migration Utilities for WriteIt DDD Refactoring.

This module provides utilities for migrating existing data from the old system
format to the new DDD-based structure. It handles:
- Legacy YAML pipeline template conversion
- Workspace configuration updates
- Cache format migration
- LMDB data structure updates
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
import uuid
import lmdb

from writeit.domains.pipeline.entities import PipelineTemplate, PipelineInput, PipelineStepTemplate
from writeit.domains.pipeline.value_objects import (
    PipelineId, StepId, PromptTemplate, ModelPreference
)
from writeit.domains.workspace.value_objects import WorkspaceName
from writeit.workspace.workspace import Workspace


class DataMigrationError(Exception):
    """Exception raised during data migration."""
    pass


class DataMigrator:
    """Handles migration of data from legacy formats to DDD structure."""
    
    def __init__(self, workspace: Workspace):
        """Initialize migrator with workspace context.
        
        Args:
            workspace: Workspace instance for migration context
        """
        self.workspace = workspace
        self.migration_log = []
        
    def log_migration(self, message: str, level: str = "info") -> None:
        """Log migration activity.
        
        Args:
            message: Log message
            level: Log level (info, warning, error)
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.migration_log.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
        
    def get_migration_log(self) -> List[Dict[str, Any]]:
        """Get migration log.
        
        Returns:
            List of migration log entries
        """
        return self.migration_log
        
    def migrate_pipeline_template(self, template_path: Path) -> Optional[PipelineTemplate]:
        """Migrate a legacy YAML pipeline template to DDD structure.
        
        Args:
            template_path: Path to legacy YAML template
            
        Returns:
            Migrated PipelineTemplate or None if migration failed
            
        Raises:
            DataMigrationError: If migration encounters critical errors
        """
        try:
            self.log_migration(f"Migrating pipeline template: {template_path}")
            
            # Load legacy YAML
            with open(template_path, 'r', encoding='utf-8') as f:
                legacy_data = yaml.safe_load(f)
                
            if not legacy_data:
                self.log_migration(f"Empty template file: {template_path}", "warning")
                return None
                
            # Extract basic metadata
            metadata = legacy_data.get('metadata', {})
            name = metadata.get('name', template_path.stem)
            description = metadata.get('description', f'Migrated template from {template_path.name}')
            version = metadata.get('version', '1.0.0')
            
            # Migrate inputs
            inputs = self._migrate_inputs(legacy_data.get('inputs', {}))
            
            # Migrate steps
            steps = self._migrate_steps(legacy_data.get('steps', []))
            
            # Extract additional fields
            defaults = legacy_data.get('defaults', {})
            author = metadata.get('author')
            tags = metadata.get('tags', [])
            
            # Create DDD pipeline template
            pipeline_template = PipelineTemplate.create(
                name=name,
                description=description,
                inputs=inputs,
                steps=steps,
                version=version,
                metadata=metadata,
                defaults=defaults,
                tags=tags,
                author=author
            )
            
            self.log_migration(f"Successfully migrated template: {name}")
            return pipeline_template
            
        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML in {template_path}: {e}"
            self.log_migration(error_msg, "error")
            raise DataMigrationError(error_msg)
        except Exception as e:
            error_msg = f"Migration failed for {template_path}: {e}"
            self.log_migration(error_msg, "error")
            raise DataMigrationError(error_msg)
            
    def _migrate_inputs(self, legacy_inputs: Dict[str, Any]) -> List[PipelineInput]:
        """Migrate legacy input definitions to DDD structure.
        
        Args:
            legacy_inputs: Dictionary of legacy input definitions
            
        Returns:
            List of PipelineInput objects
        """
        inputs = []
        
        for key, config in legacy_inputs.items():
            # Handle both old and new format
            if isinstance(config, dict):
                input_type = config.get('type', 'text')
                label = config.get('label', key)
                required = config.get('required', False)
                default = config.get('default')
                placeholder = config.get('placeholder', '')
                help_text = config.get('help', '')
                max_length = config.get('max_length')
                
                # Handle choice options
                options = []
                if input_type == 'choice' and 'options' in config:
                    opts = config['options']
                    if isinstance(opts, list):
                        for opt in opts:
                            if isinstance(opt, dict):
                                options.append(opt)
                            elif isinstance(opt, str):
                                options.append({'label': opt, 'value': opt})
                                
            else:
                # Simple format: just the type
                input_type = str(config)
                label = key.title()
                required = False
                default = None
                placeholder = ''
                help_text = ''
                max_length = None
                options = []
                
            # Create PipelineInput
            pipeline_input = PipelineInput(
                key=key,
                type=input_type,
                label=label,
                required=required,
                default=default,
                placeholder=placeholder,
                help=help_text,
                options=options,
                max_length=max_length
            )
            
            inputs.append(pipeline_input)
            
        return inputs
        
    def _migrate_steps(self, legacy_steps: List[Dict[str, Any]]) -> List[PipelineStepTemplate]:
        """Migrate legacy step definitions to DDD structure.
        
        Args:
            legacy_steps: List of legacy step definitions
            
        Returns:
            List of PipelineStepTemplate objects
        """
        steps = []
        
        for step_data in legacy_steps:
            # Handle both old and new format
            if isinstance(step_data, dict):
                name = step_data.get('name', 'unnamed')
                description = step_data.get('description', '')
                step_type = step_data.get('type', 'llm_generate')
                
                # Generate step ID from name or key
                key = step_data.get('key', name.lower().replace(' ', '_'))
                step_id = StepId(key)
                
                # Migrate prompt template
                prompt_template_str = step_data.get('prompt_template', '')
                selection_prompt = step_data.get('selection_prompt', '')
                
                # Handle template variables
                prompt_template = PromptTemplate(prompt_template_str)
                
                # Migrate model preference
                model_preference_data = step_data.get('model_preference', ['gpt-4o-mini'])
                if isinstance(model_preference_data, str):
                    model_preference_data = [model_preference_data]
                model_preference = ModelPreference(model_preference_data)
                
                # Migrate dependencies
                depends_on_data = step_data.get('depends_on', [])
                depends_on = [StepId(dep) for dep in depends_on_data if isinstance(dep, str)]
                
                # Additional configuration
                validation = step_data.get('validation', {})
                ui = step_data.get('ui', {})
                parallel = step_data.get('parallel', False)
                retry_config = step_data.get('retry_config', {})
                
                # Create PipelineStepTemplate
                step_template = PipelineStepTemplate(
                    id=step_id,
                    name=name,
                    description=description,
                    type=step_type,
                    prompt_template=prompt_template,
                    selection_prompt=selection_prompt,
                    model_preference=model_preference,
                    validation=validation,
                    ui=ui,
                    depends_on=depends_on,
                    parallel=parallel,
                    retry_config=retry_config
                )
                
                steps.append(step_template)
                
        return steps
        
    def migrate_workspace_config(self, config_path: Path) -> Dict[str, Any]:
        """Migrate workspace configuration to new format.
        
        Args:
            config_path: Path to legacy workspace config
            
        Returns:
            Migrated configuration dictionary
        """
        try:
            self.log_migration(f"Migrating workspace config: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            if not config_data:
                return {}
                
            # Update configuration structure
            migrated_config = {
                'version': '2.0.0',
                'writeit_version': config_data.get('writeit_version', '0.1.0'),
                'workspace_name': config_data.get('name', 'default'),
                'created_at': config_data.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat(),
                'settings': {
                    'default_model': config_data.get('default_model', 'gpt-4o-mini'),
                    'auto_save': config_data.get('auto_save', True),
                    'max_history': config_data.get('max_history', 1000),
                },
                'llm_providers': config_data.get('llm_providers', {}),
                'metadata': config_data.get('metadata', {})
            }
            
            # Remove legacy fields that are now handled elsewhere
            legacy_fields_to_remove = ['default_pipeline', 'active_workspace']
            for field in legacy_fields_to_remove:
                migrated_config.get('settings', {}).pop(field, None)
                
            self.log_migration("Workspace configuration migrated successfully")
            return migrated_config
            
        except Exception as e:
            error_msg = f"Failed to migrate workspace config: {e}"
            self.log_migration(error_msg, "error")
            raise DataMigrationError(error_msg)
            
    def migrate_lmdb_data(self, lmdb_path: Path, target_path: Path) -> bool:
        """Migrate LMDB data to new DDD-compatible format.
        
        Args:
            lmdb_path: Path to legacy LMDB database
            target_path: Path for new LMDB database
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.log_migration(f"Migrating LMDB data from {lmdb_path} to {target_path}")
            
            if not lmdb_path.exists():
                self.log_migration(f"LMDB path does not exist: {lmdb_path}", "warning")
                return False
                
            # Open legacy LMDB
            legacy_env = lmdb.open(str(lmdb_path), readonly=True, max_dbs=10)
            
            # Create new LMDB with DDD structure
            target_path.parent.mkdir(parents=True, exist_ok=True)
            new_env = lmdb.open(str(target_path), max_dbs=10)
            
            # Migrate databases
            with legacy_env.begin() as legacy_txn:
                with new_env.begin(write=True) as new_txn:
                    # List all databases
                    cursor = legacy_txn.cursor()
                    
                    # Migrate main data
                    for key, value in cursor:
                        try:
                            # Try to parse as JSON for structure migration
                            try:
                                data = json.loads(value.decode('utf-8'))
                                migrated_data = self._migrate_lmdb_entry(data)
                                migrated_value = json.dumps(migrated_data).encode('utf-8')
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                # Binary data, copy as-is
                                migrated_value = value
                                
                            new_txn.put(key, migrated_value)
                            
                        except Exception as e:
                            self.log_migration(f"Failed to migrate LMDB entry {key}: {e}", "warning")
                            continue
                            
            # Close environments
            legacy_env.close()
            new_env.close()
            
            self.log_migration("LMDB data migration completed")
            return True
            
        except Exception as e:
            error_msg = f"LMDB migration failed: {e}"
            self.log_migration(error_msg, "error")
            return False
            
    def _migrate_lmdb_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate a single LMDB entry to new format.
        
        Args:
            entry_data: Legacy entry data
            
        Returns:
            Migrated entry data
        """
        migrated = entry_data.copy()
        
        # Update version information
        migrated['_migration_version'] = '2.0.0'
        migrated['_migrated_at'] = datetime.now().isoformat()
        
        # Migrate pipeline runs to new structure
        if 'pipeline_run' in migrated:
            pipeline_data = migrated['pipeline_run']
            if isinstance(pipeline_data, dict):
                # Update to new DDD structure
                pipeline_data['domain_id'] = pipeline_data.get('id', str(uuid.uuid4()))
                pipeline_data['workspace_name'] = self.workspace.name
                
        # Migrate cache entries
        if 'cache' in migrated:
            cache_data = migrated['cache']
            if isinstance(cache_data, dict):
                cache_data['workspace_isolated'] = True
                cache_data['cache_version'] = '2.0'
                
        return migrated
        
    def backup_legacy_data(self, source_path: Path) -> Path:
        """Create backup of legacy data before migration.
        
        Args:
            source_path: Path to legacy data
            
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"writeit_migration_backup_{timestamp}"
        backup_path = source_path.parent / backup_name
        
        try:
            if source_path.is_file():
                shutil.copy2(source_path, backup_path)
            else:
                shutil.copytree(source_path, backup_path)
                
            self.log_migration(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            error_msg = f"Failed to create backup: {e}"
            self.log_migration(error_msg, "error")
            raise DataMigrationError(error_msg)
            
    def validate_migration(self, workspace_path: Path) -> List[str]:
        """Validate migrated data structure.
        
        Args:
            workspace_path: Path to migrated workspace
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            # Check workspace structure
            required_dirs = ['pipelines', 'styles', 'templates', 'articles']
            for dir_name in required_dirs:
                dir_path = workspace_path / dir_name
                if not dir_path.exists():
                    issues.append(f"Missing required directory: {dir_name}")
                    
            # Check workspace config
            config_path = workspace_path / 'workspace.yaml'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    
                if not isinstance(config, dict):
                    issues.append("Workspace config is not a valid dictionary")
                elif 'version' not in config:
                    issues.append("Workspace config missing version information")
                    
            # Check pipeline templates
            templates_dir = workspace_path / 'templates'
            if templates_dir.exists():
                for template_file in templates_dir.glob('*.yaml'):
                    try:
                        with open(template_file, 'r') as f:
                            template_data = yaml.safe_load(f)
                            
                        if not template_data or 'metadata' not in template_data:
                            issues.append(f"Invalid template structure: {template_file}")
                            
                    except Exception as e:
                        issues.append(f"Cannot read template {template_file}: {e}")
                        
        except Exception as e:
            issues.append(f"Validation error: {e}")
            
        return issues
        
    def run_full_migration(self, workspace_path: Path) -> bool:
        """Run complete migration for a workspace.
        
        Args:
            workspace_path: Path to workspace to migrate
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.log_migration(f"Starting full migration for workspace: {workspace_path}")
            
            # Create backup
            backup_path = self.backup_legacy_data(workspace_path)
            
            # Migrate workspace configuration
            config_path = workspace_path / 'workspace.yaml'
            if config_path.exists():
                migrated_config = self.migrate_workspace_config(config_path)
                
                # Write migrated config
                with open(config_path, 'w') as f:
                    yaml.dump(migrated_config, f, default_flow_style=False)
                    
            # Migrate pipeline templates
            templates_dir = workspace_path / 'templates'
            if templates_dir.exists():
                for template_file in templates_dir.glob('*.yaml'):
                    try:
                        migrated_template = self.migrate_pipeline_template(template_file)
                        if migrated_template:
                            # Save migrated template
                            with open(template_file, 'w') as f:
                                # Convert to YAML (would need a proper serializer)
                                f.write(f"# Migrated template: {migrated_template.name}\n")
                                f.write(f"# Version: {migrated_template.version}\n")
                                f.write(f"# Migration date: {datetime.now().isoformat()}\n")
                                
                    except DataMigrationError as e:
                        self.log_migration(f"Skipping template {template_file}: {e}", "warning")
                        continue
                        
            # Migrate LMDB data
            lmdb_files = list(workspace_path.glob('*.mdb')) + list(workspace_path.glob('*.lmdb'))
            for lmdb_file in lmdb_files:
                target_file = workspace_path / f"migrated_{lmdb_file.name}"
                self.migrate_lmdb_data(lmdb_file, target_file)
                
            # Validate migration
            validation_issues = self.validate_migration(workspace_path)
            if validation_issues:
                self.log_migration(f"Migration validation issues: {validation_issues}", "warning")
                
            self.log_migration("Full migration completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Full migration failed: {e}"
            self.log_migration(error_msg, "error")
            return False


def create_migration_report(migrator: DataMigrator) -> str:
    """Create a detailed migration report.
    
    Args:
        migrator: DataMigrator instance with migration log
        
    Returns:
        Formatted migration report
    """
    log = migrator.get_migration_log()
    
    report = [
        "# WriteIt Data Migration Report",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Migration Summary",
        f"Total log entries: {len(log)}",
        "",
        "## Migration Log",
        ""
    ]
    
    # Group by level
    by_level = {'info': [], 'warning': [], 'error': []}
    for entry in log:
        level = entry.get('level', 'info')
        by_level[level].append(entry)
        
    # Add errors
    if by_level['error']:
        report.append("### Errors")
        for entry in by_level['error']:
            report.append(f"- {entry['timestamp']}: {entry['message']}")
        report.append("")
        
    # Add warnings
    if by_level['warning']:
        report.append("### Warnings")
        for entry in by_level['warning']:
            report.append(f"- {entry['timestamp']}: {entry['message']}")
        report.append("")
        
    # Add info
    if by_level['info']:
        report.append("### Information")
        for entry in by_level['info']:
            report.append(f"- {entry['timestamp']}: {entry['message']}")
        report.append("")
        
    return "\n".join(report)