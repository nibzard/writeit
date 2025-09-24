"""Workspace Structure Updater for WriteIt DDD Migration.

This module handles the migration of workspace directory structures from the old format
to the new DDD-compatible structure. It ensures proper organization of workspace data
according to DDD principles.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import yaml

from writeit.workspace.workspace import Workspace
from dataclasses import dataclass, field
from typing import List


@dataclass
class WorkspaceStructureUpdateResult:
    """Result of workspace structure update."""
    
    success: bool
    message: str
    updated_directories: int = 0
    created_files: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    backup_path: Optional[Path] = None


class WorkspaceStructureUpdater:
    """Updates workspace directory structure to DDD format."""
    
    def __init__(self, workspace: Workspace):
        """Initialize workspace structure updater.
        
        Args:
            workspace: Workspace instance
        """
        self.workspace = workspace
        self.update_log = []
        self.backup_created = False
        
    def log_update(self, message: str, level: str = "info") -> None:
        """Log structure update activity."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.update_log.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
        
    def get_update_log(self) -> List[Dict[str, Any]]:
        """Get update log.
        
        Returns:
            List of update log entries
        """
        return self.update_log
        
    def update_workspace_structure(self, workspace_name: str) -> WorkspaceStructureUpdateResult:
        """Update workspace directory structure to DDD format.
        
        Args:
            workspace_name: Name of workspace to update
            
        Returns:
            Update result with success status and details
        """
        result = WorkspaceStructureUpdateResult(
            success=False,
            message=f"Workspace structure update for {workspace_name}"
        )
        
        try:
            self.log_update(f"Updating workspace structure: {workspace_name}")
            
            # Get workspace path
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            
            if not workspace_path.exists():
                self.log_update(f"Workspace not found: {workspace_path}", "error")
                result.message = f"Workspace not found: {workspace_path}"
                return result
                
            # Create backup before making changes
            if not self.backup_created:
                result.backup_path = self._create_workspace_backup(workspace_path)
                self.backup_created = True
                
            # Update structure
            update_success = self._perform_structure_update(workspace_path)
            
            if update_success:
                result.success = True
                result.message = f"Successfully updated workspace structure: {workspace_name}"
                self.log_update(result.message)
            else:
                result.message = f"Failed to update workspace structure: {workspace_name}"
                self.log_update(result.message, "error")
                
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"Error updating workspace structure {workspace_name}: {e}"
            result.errors.append(str(e))
            self.log_update(result.message, "error")
            return result
            
    def _create_workspace_backup(self, workspace_path: Path) -> Path:
        """Create backup of workspace before structure update.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace_name = workspace_path.name
        backup_name = f"workspace_structure_backup_{workspace_name}_{timestamp}"
        backup_path = workspace_path.parent / backup_name
        
        try:
            shutil.copytree(workspace_path, backup_path)
            self.log_update(f"Created workspace backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.log_update(f"Failed to create backup: {e}", "error")
            raise ValueError(f"Backup creation failed: {e}")
            
    def _perform_structure_update(self, workspace_path: Path) -> bool:
        """Perform the actual structure update.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Define DDD-compliant directory structure
            ddd_structure = {
                "pipelines": {
                    "templates": True,  # Directory for pipeline templates
                    "runs": True,       # Directory for pipeline run data
                    "exports": True     # Directory for exported results
                },
                "workspace": {
                    "data": True,       # Workspace-specific data
                    "config": True,     # Workspace configuration
                    "cache": True,      # Workspace cache
                    "logs": True        # Workspace logs
                },
                "domains": {
                    "pipeline": True,   # Pipeline domain data
                    "workspace": True,  # Workspace domain data
                    "llm": True         # LLM domain data
                },
                "storage": {
                    "lmdb": True,       # LMDB storage
                    "files": True,      # File storage
                    "temp": True        # Temporary files
                },
                "templates": True,     # Legacy templates (keep for compatibility)
                "styles": True,        # Style primers
                "articles": True,      # Generated articles
                "cache": True,         # Cache directory
                "logs": True           # Log files
            }
            
            # Create DDD directory structure
            created_dirs = self._create_ddd_directories(workspace_path, ddd_structure)
            
            # Move existing files to new structure
            moved_files = self._migrate_existing_files(workspace_path)
            
            # Update workspace configuration
            config_updated = self._update_workspace_config(workspace_path)
            
            # Create domain-specific organization
            domain_org_created = self._create_domain_organization(workspace_path)
            
            # Create storage organization
            storage_org_created = self._create_storage_organization(workspace_path)
            
            # Clean up old structure
            cleanup_completed = self._cleanup_old_structure(workspace_path)
            
            success = all([
                len(created_dirs) > 0,
                moved_files,
                config_updated,
                domain_org_created,
                storage_org_created,
                cleanup_completed
            ])
            
            if success:
                self.log_update(f"Structure update completed successfully")
                self.log_update(f"Created {len(created_dirs)} directories")
                self.log_update(f"Migrated existing files: {moved_files}")
            else:
                self.log_update("Structure update completed with some issues", "warning")
                
            return success
            
        except Exception as e:
            self.log_update(f"Structure update failed: {e}", "error")
            return False
            
    def _create_ddd_directories(self, workspace_path: Path, structure: Dict[str, Any]) -> List[Path]:
        """Create DDD-compliant directory structure.
        
        Args:
            workspace_path: Path to workspace
            structure: Directory structure definition
            
        Returns:
            List of created directories
        """
        created_dirs = []
        
        def create_recursive(base_path: Path, structure_def: Any, current_path: List[str] = None) -> None:
            """Recursively create directory structure."""
            if current_path is None:
                current_path = []
                
            for name, definition in structure_def.items():
                if isinstance(definition, bool):
                    # This is a directory
                    dir_path = base_path / name
                    if not dir_path.exists():
                        dir_path.mkdir(parents=True, exist_ok=True)
                        created_dirs.append(dir_path)
                        self.log_update(f"Created directory: {'/'.join(current_path + [name])}")
                        
                elif isinstance(definition, dict):
                    # This is a subdirectory with nested structure
                    sub_path = current_path + [name]
                    create_recursive(base_path / name, definition, sub_path)
                    
        create_recursive(workspace_path, structure)
        return created_dirs
        
    def _migrate_existing_files(self, workspace_path: Path) -> bool:
        """Migrate existing files to new structure.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Move pipeline templates to new location
            templates_dir = workspace_path / "templates"
            new_templates_dir = workspace_path / "pipelines" / "templates"
            
            if templates_dir.exists() and new_templates_dir.exists():
                for template_file in templates_dir.glob("*.yaml"):
                    target_file = new_templates_dir / template_file.name
                    if not target_file.exists():
                        shutil.move(str(template_file), str(target_file))
                        self.log_update(f"Moved template: {template_file.name}")
                        
            # Move cache files to new location
            cache_dir = workspace_path / "cache"
            new_cache_dir = workspace_path / "workspace" / "cache"
            
            if cache_dir.exists() and new_cache_dir.exists():
                for cache_file in cache_dir.iterdir():
                    if cache_file.is_file():
                        target_file = new_cache_dir / cache_file.name
                        if not target_file.exists():
                            shutil.move(str(cache_file), str(target_file))
                            self.log_update(f"Moved cache file: {cache_file.name}")
                            
            # Move LMDB files to new location
            lmdb_files = list(workspace_path.glob("*.mdb")) + list(workspace_path.glob("*.lmdb"))
            new_lmdb_dir = workspace_path / "storage" / "lmdb"
            
            if lmdb_files and new_lmdb_dir.exists():
                for lmdb_file in lmdb_files:
                    target_file = new_lmdb_dir / lmdb_file.name
                    if not target_file.exists():
                        shutil.move(str(lmdb_file), str(target_file))
                        self.log_update(f"Moved LMDB file: {lmdb_file.name}")
                        
            return True
            
        except Exception as e:
            self.log_update(f"Failed to migrate existing files: {e}", "error")
            return False
            
    def _update_workspace_config(self, workspace_path: Path) -> bool:
        """Update workspace configuration for new structure.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            config_path = workspace_path / "workspace.yaml"
            
            if not config_path.exists():
                self.log_update("No workspace config found, creating default", "warning")
                return self._create_default_workspace_config(workspace_path)
                
            # Load existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                
            # Update structure information
            config["structure_version"] = "2.0"
            config["structure_updated_at"] = datetime.now().isoformat()
            config["ddd_compatible"] = True
            
            # Add new structure paths
            config["structure"] = {
                "pipelines": "pipelines",
                "workspace_data": "workspace/data",
                "domains": "domains",
                "storage": "storage",
                "templates": "templates",
                "styles": "styles",
                "articles": "articles",
                "cache": "workspace/cache",
                "logs": "logs"
            }
            
            # Write updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
            self.log_update("Updated workspace configuration")
            return True
            
        except Exception as e:
            self.log_update(f"Failed to update workspace config: {e}", "error")
            return False
            
    def _create_default_workspace_config(self, workspace_path: Path) -> bool:
        """Create default workspace configuration.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            config = {
                "name": workspace_path.name,
                "structure_version": "2.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "ddd_compatible": True,
                "structure": {
                    "pipelines": "pipelines",
                    "workspace_data": "workspace/data",
                    "domains": "domains",
                    "storage": "storage",
                    "templates": "templates",
                    "styles": "styles",
                    "articles": "articles",
                    "cache": "workspace/cache",
                    "logs": "logs"
                },
                "settings": {
                    "default_model": "gpt-4o-mini",
                    "auto_save": True,
                    "max_history": 1000
                }
            }
            
            config_path = workspace_path / "workspace.yaml"
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
            self.log_update("Created default workspace configuration")
            return True
            
        except Exception as e:
            self.log_update(f"Failed to create default config: {e}", "error")
            return False
            
    def _create_domain_organization(self, workspace_path: Path) -> bool:
        """Create domain-specific organization.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            domains_dir = workspace_path / "domains"
            
            # Create domain-specific files
            domain_info = {
                "pipeline": {
                    "description": "Pipeline domain entities and value objects",
                    "entities": ["PipelineTemplate", "PipelineRun", "StepExecution"],
                    "value_objects": ["PipelineId", "StepId", "PromptTemplate", "ModelPreference"]
                },
                "workspace": {
                    "description": "Workspace domain entities and value objects", 
                    "entities": ["Workspace", "WorkspaceConfiguration"],
                    "value_objects": ["WorkspaceName", "WorkspacePath", "ConfigurationValue"]
                },
                "llm": {
                    "description": "LLM integration domain entities and value objects",
                    "entities": ["LLMModel", "LLMResponse", "LLMCache"],
                    "value_objects": ["ModelName", "Prompt", "Response"]
                }
            }
            
            for domain_name, domain_data in domain_info.items():
                domain_dir = domains_dir / domain_name
                
                # Create domain info file
                info_file = domain_dir / "domain_info.yaml"
                with open(info_file, 'w', encoding='utf-8') as f:
                    yaml.dump(domain_data, f, default_flow_style=False, allow_unicode=True)
                    
                # Create domain-specific directories
                for subdir in ["entities", "value_objects", "services", "repositories"]:
                    (domain_dir / subdir).mkdir(exist_ok=True)
                    
            self.log_update("Created domain organization")
            return True
            
        except Exception as e:
            self.log_update(f"Failed to create domain organization: {e}", "error")
            return False
            
    def _create_storage_organization(self, workspace_path: Path) -> bool:
        """Create storage organization.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            storage_dir = workspace_path / "storage"
            
            # Create storage info file
            storage_info = {
                "description": "Storage organization for workspace data",
                "lmdb_path": "lmdb",
                "file_storage_path": "files", 
                "temp_path": "temp",
                "backup_path": "backups",
                "created_at": datetime.now().isoformat(),
                "structure_version": "2.0"
            }
            
            info_file = storage_dir / "storage_info.yaml"
            with open(info_file, 'w', encoding='utf-8') as f:
                yaml.dump(storage_info, f, default_flow_style=False, allow_unicode=True)
                
            # Create storage subdirectories
            for subdir in ["backups", "exports"]:
                (storage_dir / subdir).mkdir(exist_ok=True)
                
            self.log_update("Created storage organization")
            return True
            
        except Exception as e:
            self.log_update(f"Failed to create storage organization: {e}", "error")
            return False
            
    def _cleanup_old_structure(self, workspace_path: Path) -> bool:
        """Clean up old structure files and directories.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            # Clean up empty directories
            empty_dirs = []
            
            for dir_path in workspace_path.rglob("*"):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    # Don't remove essential DDD directories
                    if not self._is_essential_ddd_directory(dir_path, workspace_path):
                        empty_dirs.append(dir_path)
                        
            # Remove empty directories
            for empty_dir in empty_dirs:
                try:
                    empty_dir.rmdir()
                    self.log_update(f"Removed empty directory: {empty_dir.relative_to(workspace_path)}")
                except OSError:
                    # Directory might have been created by another process
                    continue
                    
            # Clean up temporary files
            temp_files = []
            for pattern in ["*.tmp", "*.temp", "*.bak", "*~"]:
                temp_files.extend(workspace_path.rglob(pattern))
                
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    self.log_update(f"Removed temporary file: {temp_file.name}")
                except OSError:
                    continue
                    
            return True
            
        except Exception as e:
            self.log_update(f"Failed to cleanup old structure: {e}", "warning")
            return False
            
    def _is_essential_ddd_directory(self, dir_path: Path, workspace_path: Path) -> bool:
        """Check if directory is essential for DDD structure.
        
        Args:
            dir_path: Directory path to check
            workspace_path: Workspace root path
            
        Returns:
            True if directory is essential, False otherwise
        """
        essential_paths = {
            "pipelines",
            "workspace", 
            "domains",
            "storage",
            "templates",
            "styles",
            "articles",
            "cache",
            "logs"
        }
        
        relative_path = dir_path.relative_to(workspace_path)
        path_parts = relative_path.parts
        
        if not path_parts:
            return True  # Root directory
            
        return path_parts[0] in essential_paths
        
    def validate_updated_structure(self, workspace_path: Path) -> List[str]:
        """Validate that workspace structure has been properly updated.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Check for required DDD directories
        required_dirs = [
            "pipelines/templates",
            "workspace/data", 
            "workspace/cache",
            "domains/pipeline",
            "domains/workspace",
            "domains/llm",
            "storage/lmdb",
            "storage/files"
        ]
        
        for dir_path in required_dirs:
            full_path = workspace_path / dir_path
            if not full_path.exists():
                issues.append(f"Missing required directory: {dir_path}")
                
        # Check workspace configuration
        config_path = workspace_path / "workspace.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    
                if not config.get("ddd_compatible"):
                    issues.append("Workspace configuration not marked as DDD compatible")
                    
                if config.get("structure_version") != "2.0":
                    issues.append("Workspace structure version not updated")
                    
            except Exception as e:
                issues.append(f"Cannot read workspace configuration: {e}")
        else:
            issues.append("Workspace configuration file missing")
            
        return issues
        
    def rollback_structure_update(self, workspace_name: str) -> bool:
        """Rollback workspace structure update.
        
        Args:
            workspace_name: Name of workspace to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            
            # Find backup directory
            backup_pattern = f"workspace_structure_backup_{workspace_name}_*"
            backup_dirs = list(workspace_path.parent.glob(backup_pattern))
            
            if not backup_dirs:
                self.log_update(f"No structure backup found for workspace: {workspace_name}", "error")
                return False
                
            # Use most recent backup
            latest_backup = max(backup_dirs, key=lambda p: p.stat().st_mtime)
            
            self.log_update(f"Rolling back structure update using backup: {latest_backup}")
            
            # Remove current workspace directory
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
                
            # Restore from backup
            shutil.copytree(latest_backup, workspace_path)
            
            self.log_update(f"Successfully rolled back structure update for: {workspace_name}")
            return True
            
        except Exception as e:
            self.log_update(f"Structure rollback failed for workspace {workspace_name}: {e}", "error")
            return False