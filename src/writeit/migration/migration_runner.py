"""Main Migration Runner for WriteIt DDD Refactoring.

This module provides the main migration runner that orchestrates all data migration
activities for the DDD refactoring. It coordinates between different migration
components and provides a unified interface for the migration process.
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import shutil

from writeit.workspace.workspace import Workspace
from writeit.migration.data_migration import DataMigrator
from writeit.migration.legacy_format_converter import LegacyFormatConverter


class MigrationRunner:
    """Main migration runner that orchestrates the complete DDD migration."""
    
    def __init__(self, workspace: Optional[Workspace] = None):
        """Initialize migration runner.
        
        Args:
            workspace: Workspace instance (creates default if None)
        """
        self.workspace = workspace or Workspace()
        self.migrator = DataMigrator(self.workspace)
        self.converter = LegacyFormatConverter()
        self.migration_results = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "success": False,
            "summary": {},
            "details": {},
            "errors": []
        }
        
    def run_full_migration(self, workspace_name: Optional[str] = None) -> Dict[str, Any]:
        """Run complete DDD migration for specified workspace or all workspaces.
        
        Args:
            workspace_name: Specific workspace to migrate (None for all workspaces)
            
        Returns:
            Migration results dictionary
        """
        try:
            self.migration_results["start_time"] = datetime.now().isoformat()
            
            if workspace_name:
                # Migrate specific workspace
                result = self._migrate_single_workspace(workspace_name)
                self.migration_results["summary"] = {
                    "workspaces_attempted": 1,
                    "workspaces_succeeded": 1 if result["success"] else 0,
                    "workspaces_failed": 0 if result["success"] else 1
                }
                self.migration_results["details"][workspace_name] = result
            else:
                # Migrate all workspaces
                result = self._migrate_all_workspaces()
                self.migration_results["summary"] = result["summary"]
                self.migration_results["details"] = result["details"]
                
            self.migration_results["end_time"] = datetime.now().isoformat()
            self.migration_results["success"] = True
            
            return self.migration_results
            
        except Exception as e:
            self.migration_results["end_time"] = datetime.now().isoformat()
            self.migration_results["success"] = False
            self.migration_results["errors"].append(str(e))
            
            return self.migration_results
            
    def _migrate_single_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Migrate a single workspace.
        
        Args:
            workspace_name: Name of workspace to migrate
            
        Returns:
            Migration result for the workspace
        """
        result = {
            "workspace_name": workspace_name,
            "success": False,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "steps_completed": [],
            "errors": [],
            "files_processed": 0
        }
        
        try:
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            
            if not workspace_path.exists():
                result["errors"].append(f"Workspace path does not exist: {workspace_path}")
                return result
                
            self.migrator.log_migration(f"Starting migration for workspace: {workspace_name}")
            
            # Step 1: Backup existing data
            backup_path = self.migrator.backup_legacy_data(workspace_path)
            result["steps_completed"].append("backup_created")
            result["backup_path"] = str(backup_path)
            
            # Step 2: Migrate workspace configuration
            config_path = workspace_path / "workspace.yaml"
            if config_path.exists():
                migrated_config = self._migrate_workspace_config(config_path)
                result["steps_completed"].append("config_migrated")
                
            # Step 3: Migrate pipeline templates
            templates_dir = workspace_path / "templates"
            if templates_dir.exists():
                template_results = self._migrate_templates(templates_dir)
                result["steps_completed"].append("templates_migrated")
                result["templates_processed"] = template_results
                
            # Step 4: Migrate LMDB data
            lmdb_results = self._migrate_lmdb_data(workspace_path)
            if lmdb_results["files_processed"] > 0:
                result["steps_completed"].append("lmdb_migrated")
                result["lmdb_results"] = lmdb_results
                
            # Step 5: Validate migration
            validation_issues = self.migrator.validate_migration(workspace_path)
            if validation_issues:
                result["validation_issues"] = validation_issues
                result["warnings"] = [f"Validation issue: {issue}" for issue in validation_issues]
            else:
                result["steps_completed"].append("validation_passed")
                
            # Count files processed
            result["files_processed"] = self._count_processed_files(workspace_path)
            
            result["success"] = True
            result["end_time"] = datetime.now().isoformat()
            
            self.migrator.log_migration(f"Successfully migrated workspace: {workspace_name}")
            return result
            
        except Exception as e:
            result["end_time"] = datetime.now().isoformat()
            result["errors"].append(str(e))
            self.migrator.log_migration(f"Migration failed for workspace {workspace_name}: {e}", "error")
            return result
            
    def _migrate_all_workspaces(self) -> Dict[str, Any]:
        """Migrate all available workspaces.
        
        Returns:
            Migration results for all workspaces
        """
        workspaces = self.workspace.list_workspaces()
        
        if not workspaces:
            return {
                "summary": {
                    "workspaces_attempted": 0,
                    "workspaces_succeeded": 0,
                    "workspaces_failed": 0
                },
                "details": {}
            }
            
        results = {
            "summary": {
                "workspaces_attempted": len(workspaces),
                "workspaces_succeeded": 0,
                "workspaces_failed": 0
            },
            "details": {}
        }
        
        for workspace_name in workspaces:
            result = self._migrate_single_workspace(workspace_name)
            results["details"][workspace_name] = result
            
            if result["success"]:
                results["summary"]["workspaces_succeeded"] += 1
            else:
                results["summary"]["workspaces_failed"] += 1
                
        return results
        
    def _migrate_workspace_config(self, config_path: Path) -> Dict[str, Any]:
        """Migrate workspace configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Migrated configuration data
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                legacy_config = yaml.safe_load(f)
                
            migrated_config = self.converter.convert_workspace_config(legacy_config)
            
            # Write migrated config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(migrated_config, f, default_flow_style=False, allow_unicode=True)
                
            self.migrator.log_migration(f"Migrated workspace config: {config_path}")
            return migrated_config
            
        except Exception as e:
            self.migrator.log_migration(f"Failed to migrate workspace config {config_path}: {e}", "error")
            raise ValueError(f"Config migration failed: {e}")
            
    def _migrate_templates(self, templates_dir: Path) -> Dict[str, Any]:
        """Migrate all pipeline templates in a directory.
        
        Args:
            templates_dir: Directory containing template files
            
        Returns:
            Template migration results
        """
        results = {
            "total_templates": 0,
            "successful": 0,
            "failed": 0,
            "details": {}
        }
        
        template_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
        results["total_templates"] = len(template_files)
        
        for template_file in template_files:
            try:
                migrated_template = self.converter.convert_template_file(template_file)
                
                # Write migrated template
                self._write_migrated_template(template_file, migrated_template)
                
                results["successful"] += 1
                results["details"][template_file.name] = {
                    "status": "success",
                    "template_name": migrated_template.name,
                    "steps_count": len(migrated_template.steps)
                }
                
                self.migrator.log_migration(f"Migrated template: {template_file.name}")
                
            except Exception as e:
                results["failed"] += 1
                results["details"][template_file.name] = {
                    "status": "failed",
                    "error": str(e)
                }
                
                self.migrator.log_migration(f"Failed to migrate template {template_file.name}: {e}", "warning")
                
        return results
        
    def _write_migrated_template(self, template_path: Path, template) -> None:
        """Write migrated template to file.
        
        Args:
            template_path: Path to template file
            template: Migrated PipelineTemplate object
        """
        # Create migrated template structure
        migrated_data = {
            "metadata": {
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "author": template.author,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
                "migration_info": {
                    "migrated_at": datetime.now().isoformat(),
                    "migration_version": "2.0.0",
                    "from_format": "legacy_yaml"
                }
            },
            "inputs": [
                {
                    "key": inp.key,
                    "type": inp.type,
                    "label": inp.label,
                    "required": inp.required,
                    "default": inp.default,
                    "placeholder": inp.placeholder,
                    "help": inp.help,
                    "options": inp.options,
                    "max_length": inp.max_length,
                    "validation": inp.validation
                }
                for inp in template.inputs.values()
            ],
            "defaults": template.defaults,
            "steps": [
                {
                    "key": step.id.value,
                    "name": step.name,
                    "description": step.description,
                    "type": step.type,
                    "prompt_template": step.prompt_template.template,
                    "selection_prompt": step.selection_prompt,
                    "model_preference": step.model_preference.models,
                    "depends_on": [dep.value for dep in step.depends_on],
                    "parallel": step.parallel,
                    "validation": step.validation,
                    "ui": step.ui,
                    "retry_config": step.retry_config
                }
                for step in template.steps.values()
            ],
            "tags": template.tags
        }
        
        # Write to file
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(migrated_data, f, default_flow_style=False, allow_unicode=True)
            
    def _migrate_lmdb_data(self, workspace_path: Path) -> Dict[str, Any]:
        """Migrate LMDB data in workspace.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            LMDB migration results
        """
        results = {
            "files_processed": 0,
            "entries_migrated": 0,
            "errors": [],
            "details": {}
        }
        
        # Find LMDB files
        lmdb_files = list(workspace_path.glob("*.mdb")) + list(workspace_path.glob("*.lmdb"))
        
        for lmdb_file in lmdb_files:
            try:
                target_file = workspace_path / f"migrated_{lmdb_file.name}"
                
                # Use data migrator for LMDB migration
                success = self.migrator.migrate_lmdb_data(lmdb_file, target_file)
                
                if success:
                    results["files_processed"] += 1
                    results["details"][lmdb_file.name] = {
                        "status": "success",
                        "target_file": str(target_file)
                    }
                else:
                    results["errors"].append(f"Failed to migrate {lmdb_file.name}")
                    
            except Exception as e:
                results["errors"].append(f"Error migrating {lmdb_file.name}: {e}")
                
        return results
        
    def _count_processed_files(self, workspace_path: Path) -> int:
        """Count total files processed in workspace.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Total count of processed files
        """
        count = 0
        
        # Count YAML files
        yaml_files = list(workspace_path.rglob("*.yaml")) + list(workspace_path.rglob("*.yml"))
        count += len(yaml_files)
        
        # Count LMDB files
        lmdb_files = list(workspace_path.rglob("*.mdb")) + list(workspace_path.rglob("*.lmdb"))
        count += len(lmdb_files)
        
        return count
        
    def generate_migration_report(self, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive migration report.
        
        Args:
            output_path: Path to save report (None to return as string)
            
        Returns:
            Migration report content
        """
        report_lines = [
            "# WriteIt DDD Migration Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Migration Summary",
            f"Start Time: {self.migration_results['start_time']}",
            f"End Time: {self.migration_results.get('end_time', 'N/A')}",
            f"Success: {self.migration_results['success']}",
            "",
            "### Workspace Summary"
        ]
        
        summary = self.migration_results.get("summary", {})
        if summary:
            report_lines.extend([
                f"- Workspaces Attempted: {summary.get('workspaces_attempted', 0)}",
                f"- Workspaces Succeeded: {summary.get('workspaces_succeeded', 0)}",
                f"- Workspaces Failed: {summary.get('workspaces_failed', 0)}",
                ""
            ])
            
        # Add errors
        errors = self.migration_results.get("errors", [])
        if errors:
            report_lines.extend([
                "## Migration Errors",
                ""
            ])
            for error in errors:
                report_lines.append(f"- {error}")
            report_lines.append("")
            
        # Add workspace details
        details = self.migration_results.get("details", {})
        if details:
            report_lines.extend([
                "## Workspace Details",
                ""
            ])
            
            for workspace_name, workspace_result in details.items():
                report_lines.extend([
                    f"### {workspace_name}",
                    f"- Success: {workspace_result.get('success', False)}",
                    f"- Files Processed: {workspace_result.get('files_processed', 0)}",
                    f"- Steps Completed: {', '.join(workspace_result.get('steps_completed', []))}",
                    ""
                ])
                
                # Add errors for this workspace
                workspace_errors = workspace_result.get("errors", [])
                if workspace_errors:
                    report_lines.append("#### Errors:")
                    for error in workspace_errors:
                        report_lines.append(f"- {error}")
                    report_lines.append("")
                    
        # Add conversion log
        conversion_log = self.converter.get_conversion_log()
        if conversion_log:
            report_lines.extend([
                "## Conversion Log",
                ""
            ])
            for entry in conversion_log:
                level = entry.get("level", "info")
                timestamp = entry.get("timestamp", "N/A")
                message = entry.get("message", "N/A")
                report_lines.append(f"- [{timestamp}] {level.upper()}: {message}")
            report_lines.append("")
            
        report_content = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.migrator.log_migration(f"Migration report saved to: {output_path}")
            
        return report_content
        
    def rollback_migration(self, workspace_name: str) -> bool:
        """Rollback migration for a workspace using backup.
        
        Args:
            workspace_name: Name of workspace to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            
            # Find backup directory
            backup_dirs = list(workspace_path.parent.glob("writeit_migration_backup_*"))
            
            if not backup_dirs:
                self.migrator.log_migration(f"No backup found for workspace: {workspace_name}", "error")
                return False
                
            # Use most recent backup
            latest_backup = max(backup_dirs, key=lambda p: p.stat().st_mtime)
            
            self.migrator.log_migration(f"Rolling back migration using backup: {latest_backup}")
            
            # Restore from backup
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
                
            shutil.copytree(latest_backup, workspace_path)
            
            self.migrator.log_migration(f"Successfully rolled back migration for: {workspace_name}")
            return True
            
        except Exception as e:
            self.migrator.log_migration(f"Rollback failed for workspace {workspace_name}: {e}", "error")
            return False