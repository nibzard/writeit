# ABOUTME: Comprehensive data migration system for WriteIt DDD transformation
# ABOUTME: Handles migration from legacy data structures to new domain-driven design entities
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import json
import yaml
import shutil
from dataclasses import dataclass, field

from ..domains.workspace.entities.workspace import Workspace
from ..domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from ..domains.workspace.value_objects.workspace_name import WorkspaceName
from ..domains.workspace.value_objects.workspace_path import WorkspacePath
# Storage value objects are not needed for workspace migration
# Pipeline and content entities are not needed for workspace migration
from ..workspace import Workspace as LegacyWorkspace, WorkspaceConfig as LegacyWorkspaceConfig, GlobalConfig as LegacyGlobalConfig
from .config_migrator import ConfigMigrationManager, ConfigMigrationResult
from .cache_migrator import CacheMigrationManager, CacheMigrationResult


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    
    success: bool
    message: str
    migrated_items: int = 0
    skipped_items: int = 0
    error_items: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    backup_path: Optional[Path] = None


@dataclass
class LegacyWorkspaceData:
    """Legacy workspace data structure."""
    
    path: Path
    config: Optional[LegacyWorkspaceConfig] = None
    global_config: Optional[LegacyGlobalConfig] = None
    has_config: bool = False
    has_pipelines: bool = False
    has_articles: bool = False
    has_lmdb: bool = False
    pipeline_count: int = 0
    article_count: int = 0
    lmdb_files: List[Path] = field(default_factory=list)
    raw_config_data: Dict[str, Any] = field(default_factory=dict)


class DataFormatDetector:
    """Detects and analyzes legacy data formats."""
    
    @staticmethod
    def detect_legacy_workspaces(search_paths: Optional[List[Path]] = None) -> List[Path]:
        """Detect workspaces using legacy format.
        
        Args:
            search_paths: Paths to search (defaults to common locations)
            
        Returns:
            List of paths containing legacy workspaces
        """
        if search_paths is None:
            search_paths = [
                Path.home(),
                Path.cwd(),
                Path.home() / "Documents",
                Path.home() / "Projects",
                Path.home() / "Development",
                Path.home() / "dev",
            ]
        
        found_workspaces = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            try:
                # Look for .writeit directories (legacy format)
                for item in search_path.rglob(".writeit"):
                    if item.is_dir():
                        found_workspaces.append(item.parent)
                
                # Look for old workspace.yaml files
                for item in search_path.rglob("workspace.yaml"):
                    if item.is_file():
                        found_workspaces.append(item.parent)
                        
            except PermissionError:
                continue
        
        return list(set(found_workspaces))
    
    @staticmethod
    def analyze_legacy_workspace(workspace_path: Path) -> LegacyWorkspaceData:
        """Analyze a legacy workspace structure.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Analysis results
        """
        data = LegacyWorkspaceData(path=workspace_path)
        
        # Check for .writeit directory (legacy format)
        writeit_dir = workspace_path / ".writeit"
        if writeit_dir.exists():
            data.has_pipelines = (writeit_dir / "pipelines").exists()
            data.has_articles = (writeit_dir / "articles").exists()
            
            # Count files
            if data.has_pipelines:
                pipeline_files = list((writeit_dir / "pipelines").glob("*.yaml")) + \
                               list((writeit_dir / "pipelines").glob("*.yml"))
                data.pipeline_count = len(pipeline_files)
            
            if data.has_articles:
                article_files = list((writeit_dir / "articles").glob("*.md")) + \
                              list((writeit_dir / "articles").glob("*.txt"))
                data.article_count = len(article_files)
            
            # Check LMDB files
            lmdb_files = list(writeit_dir.glob("*.mdb")) + list(writeit_dir.glob("*.lmdb"))
            if lmdb_files:
                data.has_lmdb = True
                data.lmdb_files = lmdb_files
            
            # Load configuration
            config_file = writeit_dir / "config.yaml"
            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        data.raw_config_data = yaml.safe_load(f) or {}
                        # Fix datetime objects for config compatibility
                        config_data = data.raw_config_data.copy()
                        if 'created_at' in config_data and hasattr(config_data['created_at'], 'isoformat'):
                            config_data['created_at'] = config_data['created_at'].isoformat()
                        # Create DDD workspace config from legacy data
                        data.config = self._create_legacy_config_from_dict(config_data)
                        data.has_config = True
                except (yaml.YAMLError, TypeError):
                    pass
        
        # Check for workspace.yaml in root (old format)
        workspace_config_file = workspace_path / "workspace.yaml"
        if workspace_config_file.exists():
            try:
                with open(workspace_config_file, "r") as f:
                    config_data = yaml.safe_load(f) or {}
                    data.raw_config_data.update(config_data)
                    # Fix datetime objects for config compatibility
                    if not data.config:
                        workspace_config_data = config_data.copy()
                        if 'created_at' in workspace_config_data and hasattr(workspace_config_data['created_at'], 'isoformat'):
                            workspace_config_data['created_at'] = workspace_config_data['created_at'].isoformat()
                        data.config = self._create_legacy_config_from_dict(workspace_config_data)
                    data.has_config = True
            except (yaml.YAMLError, TypeError):
                pass
        
        return data
    
    @staticmethod
    def detect_legacy_pickle_data(storage_path: Path) -> List[str]:
        """Detect legacy pickle data in storage.
        
        Args:
            storage_path: Path to storage directory
            
        Returns:
            List of keys that contain pickle data
        """
        pickle_keys = []
        
        if not storage_path.exists():
            return pickle_keys
        
        # Check for .mdb and .lmdb files
        for db_file in storage_path.glob("*.mdb"):
            pickle_keys.extend(DataFormatDetector._scan_lmdb_for_pickle(db_file))
        
        for db_file in storage_path.glob("*.lmdb"):
            pickle_keys.extend(DataFormatDetector._scan_lmdb_for_pickle(db_file))
        
        return pickle_keys
    
    @staticmethod
    def _scan_lmdb_for_pickle(db_file: Path) -> List[str]:
        """Scan LMDB file for pickle data."""
        pickle_keys = []
        
        try:
            import lmdb
            
            with lmdb.open(str(db_file), readonly=True, lock=False) as env:
                with env.begin() as txn:
                    cursor = txn.cursor()
                    for key, value in cursor:
                        # Check for pickle magic numbers
                        if value.startswith(b'\x80\x03') or value.startswith(b'\x80\x04'):
                            pickle_keys.append(key.decode('utf-8', errors='ignore'))
        except (lmdb.Error, OSError):
            pass
        
        return pickle_keys
    
    def _create_legacy_config_from_dict(self, config_data: Dict[str, Any]) -> 'LegacyWorkspaceConfig':
        """Create a legacy config object from dictionary data.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            LegacyWorkspaceConfig instance
        """
        # Create a minimal LegacyWorkspaceConfig with just the fields we need
        config = LegacyWorkspaceConfig()
        
        # Store the legacy data as attributes for migration
        for key, value in config_data.items():
            setattr(config, f"legacy_{key}", value)
        
        # Set some default values
        if not hasattr(config, 'legacy_name'):
            config.legacy_name = "Migrated Workspace"
        if not hasattr(config, 'legacy_created_at'):
            config.legacy_created_at = datetime.now().isoformat()
        
        return config


class WorkspaceDataMigrator:
    """Migrates workspace data from legacy to DDD format."""
    
    def __init__(self, workspace_manager=None):
        """Initialize migrator.
        
        Args:
            workspace_manager: Workspace manager instance
        """
        self.workspace_manager = workspace_manager
        self.detector = DataFormatDetector()
        self.config_migrator = ConfigMigrationManager()
        self.cache_migrator = CacheMigrationManager()
    
    def migrate_workspace(
        self, 
        legacy_path: Path, 
        target_name: Optional[str] = None,
        overwrite: bool = False,
        backup: bool = True
    ) -> MigrationResult:
        """Migrate a legacy workspace to new DDD format.
        
        Args:
            legacy_path: Path to legacy workspace
            target_name: Name for new workspace (auto-generated if None)
            overwrite: Whether to overwrite existing workspace
            backup: Whether to create backup before migration
            
        Returns:
            Migration result
        """
        try:
            # Analyze legacy workspace
            legacy_data = self.detector.analyze_legacy_workspace(legacy_path)
            
            # Generate workspace name if not provided
            if target_name is None:
                target_name = self._generate_workspace_name(legacy_path)
            
            # Create backup if requested
            backup_path = None
            if backup:
                backup_path = self._create_backup(legacy_path)
            
            # Check if target exists
            if self._workspace_exists(target_name) and not overwrite:
                return MigrationResult(
                    success=False,
                    message=f"Workspace '{target_name}' already exists",
                    backup_path=backup_path
                )
            
            # Create new DDD workspace
            workspace = self._create_ddd_workspace(target_name, legacy_data)
            
            # Migrate data
            migrated_count = 0
            warnings = []
            errors = []
            
            # Migrate pipelines
            if legacy_data.has_pipelines:
                pipeline_result = self._migrate_pipelines(legacy_path, workspace)
                migrated_count += pipeline_result.migrated_items
                warnings.extend(pipeline_result.warnings)
                errors.extend(pipeline_result.errors)
            
            # Migrate articles/templates
            if legacy_data.has_articles:
                template_result = self._migrate_templates(legacy_path, workspace)
                migrated_count += template_result.migrated_items
                warnings.extend(template_result.warnings)
                errors.extend(template_result.errors)
            
            # Migrate LMDB data
            if legacy_data.has_lmdb:
                lmdb_result = self._migrate_lmdb_data(legacy_path, workspace)
                migrated_count += lmdb_result.migrated_items
                warnings.extend(lmdb_result.warnings)
                errors.extend(lmdb_result.errors)
            
            # Migrate cache data
            cache_result = self._migrate_cache_data(legacy_path, workspace)
            migrated_count += cache_result.migrated_items
            warnings.extend(cache_result.warnings)
            errors.extend(cache_result.errors)
            
            # Migrate configuration
            config_result = self._migrate_configuration(legacy_path, workspace)
            warnings.extend(config_result.warnings)
            errors.extend(config_result.errors)
            migrated_count += config_result.migrated_items
            
            success = len(errors) == 0
            message = f"Successfully migrated workspace '{target_name}'" if success else \
                     f"Migration completed with {len(errors)} errors"
            
            return MigrationResult(
                success=success,
                message=message,
                migrated_items=migrated_count,
                warnings=warnings,
                errors=errors,
                backup_path=backup_path
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Migration failed: {str(e)}",
                errors=[str(e)],
                backup_path=backup_path
            )
    
    def _workspace_exists(self, name: str) -> bool:
        """Check if workspace exists."""
        if self.workspace_manager:
            return self.workspace_manager.workspace_exists(name)
        return False
    
    def _generate_workspace_name(self, legacy_path: Path) -> str:
        """Generate workspace name from legacy path."""
        name = legacy_path.name.lower()
        name = name.replace(" ", "_").replace("-", "_")
        name = "".join(c for c in name if c.isalnum() or c == "_")
        
        if not name or not (name[0].isalpha() or name[0] == "_"):
            name = f"migrated_workspace_{int(datetime.now().timestamp())}"
        
        return name
    
    def _create_backup(self, legacy_path: Path) -> Path:
        """Create backup of legacy workspace."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"writeit_migration_backup_{legacy_path.name}_{timestamp}"
        
        if (legacy_path / ".writeit").exists():
            backup_path = legacy_path.parent / backup_name
            shutil.copytree(legacy_path / ".writeit", backup_path)
        else:
            backup_path = legacy_path.parent / backup_name
            shutil.copytree(legacy_path, backup_path)
        
        return backup_path
    
    def _create_ddd_workspace(
        self, 
        name: str, 
        legacy_data: LegacyWorkspaceData
    ) -> Workspace:
        """Create new DDD workspace from legacy data."""
        workspace_name = WorkspaceName.from_user_input(name)
        
        # Create root path in new structure
        if self.workspace_manager:
            base_path = Path(self.workspace_manager.workspaces_dir)
        else:
            base_path = Path.home() / ".writeit" / "workspaces"
        
        root_path = WorkspacePath(base_path / name)
        
        # Create configuration from legacy data
        if legacy_data.config:
            config = self._convert_legacy_config(legacy_data.config)
        else:
            config = WorkspaceConfiguration.default()
        
        # Create workspace
        workspace = Workspace.create(
            name=workspace_name,
            root_path=root_path,
            configuration=config,
            metadata={"migrated_from": str(legacy_data.path), "migration_date": datetime.now().isoformat()}
        )
        
        return workspace
    
    def _convert_legacy_config(self, legacy_config: LegacyWorkspaceConfig) -> WorkspaceConfiguration:
        """Convert legacy configuration to DDD format."""
        new_config = WorkspaceConfiguration.default()
        
        # Map legacy configuration values
        if legacy_config.default_pipeline:
            new_config = new_config.set_value("default_pipeline", legacy_config.default_pipeline)
        
        # Convert LLM provider configurations
        for provider, config in legacy_config.llm_providers.items():
            if provider == "openai" and isinstance(config, str):
                new_config = new_config.set_value("openai_api_key", config)
            elif provider == "anthropic" and isinstance(config, str):
                new_config = new_config.set_value("anthropic_api_key", config)
        
        return new_config
    
    def _migrate_pipelines(self, legacy_path: Path, workspace: Workspace) -> MigrationResult:
        """Migrate pipeline files."""
        result = MigrationResult(success=True, message="Pipeline migration")
        
        legacy_pipelines_dir = legacy_path / ".writeit" / "pipelines"
        new_pipelines_dir = workspace.get_pipelines_path().value
        
        if not legacy_pipelines_dir.exists():
            return result
        
        try:
            new_pipelines_dir.mkdir(parents=True, exist_ok=True)
            
            for pipeline_file in legacy_pipelines_dir.glob("*.yaml"):
                try:
                    # Validate and convert pipeline format
                    with open(pipeline_file, "r") as f:
                        pipeline_data = yaml.safe_load(f)
                    
                    # Convert to new format if needed
                    converted_data = self._convert_pipeline_format(pipeline_data)
                    
                    # Save to new location
                    target_file = new_pipelines_dir / pipeline_file.name
                    with open(target_file, "w") as f:
                        yaml.dump(converted_data, f, default_flow_style=False)
                    
                    result.migrated_items += 1
                    
                except Exception as e:
                    result.errors.append(f"Failed to migrate {pipeline_file.name}: {str(e)}")
                    result.error_items += 1
            
            for pipeline_file in legacy_pipelines_dir.glob("*.yml"):
                try:
                    # Similar handling for .yml files
                    with open(pipeline_file, "r") as f:
                        pipeline_data = yaml.safe_load(f)
                    
                    converted_data = self._convert_pipeline_format(pipeline_data)
                    
                    target_file = new_pipelines_dir / f"{pipeline_file.stem}.yaml"
                    with open(target_file, "w") as f:
                        yaml.dump(converted_data, f, default_flow_style=False)
                    
                    result.migrated_items += 1
                    
                except Exception as e:
                    result.errors.append(f"Failed to migrate {pipeline_file.name}: {str(e)}")
                    result.error_items += 1
                    
        except Exception as e:
            result.success = False
            result.errors.append(f"Pipeline migration failed: {str(e)}")
        
        return result
    
    def _migrate_templates(self, legacy_path: Path, workspace: Workspace) -> MigrationResult:
        """Migrate template files."""
        result = MigrationResult(success=True, message="Template migration")
        
        legacy_templates_dir = legacy_path / ".writeit" / "articles"
        new_templates_dir = workspace.get_templates_path().value
        
        if not legacy_templates_dir.exists():
            return result
        
        try:
            new_templates_dir.mkdir(parents=True, exist_ok=True)
            
            for template_file in legacy_templates_dir.glob("*.md"):
                try:
                    shutil.copy2(template_file, new_templates_dir)
                    result.migrated_items += 1
                except Exception as e:
                    result.errors.append(f"Failed to copy {template_file.name}: {str(e)}")
                    result.error_items += 1
            
            for template_file in legacy_templates_dir.glob("*.txt"):
                try:
                    shutil.copy2(template_file, new_templates_dir)
                    result.migrated_items += 1
                except Exception as e:
                    result.errors.append(f"Failed to copy {template_file.name}: {str(e)}")
                    result.error_items += 1
                    
        except Exception as e:
            result.success = False
            result.errors.append(f"Template migration failed: {str(e)}")
        
        return result
    
    def _migrate_lmdb_data(self, legacy_path: Path, workspace: Workspace) -> MigrationResult:
        """Migrate LMDB data."""
        result = MigrationResult(success=True, message="LMDB migration")
        
        legacy_lmdb_dir = legacy_path / ".writeit"
        new_storage_dir = workspace.get_storage_path().value
        
        if not legacy_lmdb_dir.exists():
            return result
        
        try:
            new_storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy LMDB files
            for lmdb_file in legacy_lmdb_dir.glob("*.mdb"):
                try:
                    # Check for pickle data and warn
                    pickle_keys = self.detector._scan_lmdb_for_pickle(lmdb_file)
                    if pickle_keys:
                        result.warnings.append(
                            f"Pickle data detected in {lmdb_file.name}. "
                            f"Keys: {', '.join(pickle_keys[:5])}{'...' if len(pickle_keys) > 5 else ''}. "
                            "This data cannot be migrated for security reasons."
                        )
                    
                    shutil.copy2(lmdb_file, new_storage_dir)
                    result.migrated_items += 1
                    
                except Exception as e:
                    result.errors.append(f"Failed to copy {lmdb_file.name}: {str(e)}")
                    result.error_items += 1
            
            for lmdb_file in legacy_lmdb_dir.glob("*.lmdb"):
                try:
                    pickle_keys = self.detector._scan_lmdb_for_pickle(lmdb_file)
                    if pickle_keys:
                        result.warnings.append(
                            f"Pickle data detected in {lmdb_file.name}. "
                            f"Keys: {', '.join(pickle_keys[:5])}{'...' if len(pickle_keys) > 5 else ''}. "
                            "This data cannot be migrated for security reasons."
                        )
                    
                    shutil.copy2(lmdb_file, new_storage_dir)
                    result.migrated_items += 1
                    
                except Exception as e:
                    result.errors.append(f"Failed to copy {lmdb_file.name}: {str(e)}")
                    result.error_items += 1
                    
        except Exception as e:
            result.success = False
            result.errors.append(f"LMDB migration failed: {str(e)}")
        
        return result
    
    def _migrate_configuration(self, legacy_path: Path, workspace: Workspace) -> MigrationResult:
        """Migrate workspace configuration."""
        result = MigrationResult(success=True, message="Configuration migration")
        
        try:
            # Use config migrator to handle the migration
            config_results = self.config_migrator.migrate_workspace_configs(
                legacy_path,
                backup=True,
                dry_run=False
            )
            
            if config_results:
                # Use the first successful result
                successful_configs = [r for r in config_results if r.success]
                if successful_configs:
                    config_result = successful_configs[0]
                    result.success = config_result.success
                    result.message = config_result.message
                    result.migrated_items = config_result.migrated_keys
                    result.warnings.extend(config_result.warnings)
                    result.errors.extend(config_result.errors)
                else:
                    # All config migrations failed
                    result.success = False
                    result.message = "Configuration migration failed"
                    for config_result in config_results:
                        result.errors.extend(config_result.errors)
            else:
                # No config files found, save default configuration
                config_file = workspace.get_config_path().value
                config_data = workspace.configuration.to_dict()
                
                with open(config_file, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                
                result.migrated_items = 1
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Configuration migration failed: {str(e)}")
        
        return result
    
    def _migrate_cache_data(self, legacy_path: Path, workspace: Workspace) -> MigrationResult:
        """Migrate cache data."""
        result = MigrationResult(success=True, message="Cache migration")
        
        try:
            # Use cache migrator to handle the migration
            cache_results = self.cache_migrator.migrate_workspace_cache(
                legacy_path,
                backup=True,
                skip_pickle=True,  # Skip pickle data for security
                cleanup_expired=True,
                dry_run=False
            )
            
            if cache_results:
                # Combine all cache migration results
                for cache_result in cache_results:
                    result.migrated_items += cache_result.migrated_entries
                    result.warnings.extend(cache_result.warnings)
                    result.errors.extend(cache_result.errors)
                    
                    if cache_result.pickle_entries > 0:
                        result.warnings.append(
                            f"Skipped {cache_result.pickle_entries} pickle cache entries for security reasons"
                        )
            else:
                # No cache files found
                result.migrated_items = 0
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Cache migration failed: {str(e)}")
        
        return result
    
    def _convert_pipeline_format(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert pipeline format to new DDD structure."""
        # This is a placeholder for pipeline format conversion
        # In a real implementation, this would handle format differences
        # between legacy and new pipeline structures
        
        converted = pipeline_data.copy()
        
        # Ensure required fields exist
        if "metadata" not in converted:
            converted["metadata"] = {
                "name": converted.get("name", "Unknown Pipeline"),
                "description": converted.get("description", ""),
                "version": converted.get("version", "1.0.0")
            }
        
        if "steps" not in converted:
            converted["steps"] = {}
        
        return converted


class MigrationManager:
    """High-level migration manager."""
    
    def __init__(self, workspace_manager=None):
        """Initialize migration manager."""
        self.workspace_manager = workspace_manager
        self.migrator = WorkspaceDataMigrator(workspace_manager)
        self.detector = DataFormatDetector()
    
    def scan_for_migrations(self, search_paths: Optional[List[Path]] = None) -> List[Path]:
        """Scan for workspaces that need migration."""
        return self.detector.detect_legacy_workspaces(search_paths)
    
    def migrate_all(
        self, 
        search_paths: Optional[List[Path]] = None,
        interactive: bool = False,
        backup: bool = True
    ) -> List[MigrationResult]:
        """Migrate all detected legacy workspaces."""
        legacy_workspaces = self.scan_for_migrations(search_paths)
        results = []
        
        for workspace_path in legacy_workspaces:
            if interactive:
                legacy_data = self.detector.analyze_legacy_workspace(workspace_path)
                
                print(f"\nFound legacy workspace: {workspace_path}")
                print(f"  - Pipelines: {legacy_data.pipeline_count}")
                print(f"  - Articles: {legacy_data.article_count}")
                print(f"  - Has LMDB data: {legacy_data.has_lmdb}")
                
                response = input("Migrate this workspace? (y/n): ").lower().strip()
                if response != "y":
                    results.append(MigrationResult(
                        success=False,
                        message="Skipped by user",
                        backup_path=None
                    ))
                    continue
            
            result = self.migrator.migrate_workspace(
                workspace_path,
                backup=backup
            )
            results.append(result)
        
        return results
    
    def validate_migration(self, workspace_name: str) -> MigrationResult:
        """Validate that a migration was successful."""
        try:
            # Check if workspace exists in new format
            if not self._workspace_exists(workspace_name):
                return MigrationResult(
                    success=False,
                    message=f"Workspace '{workspace_name}' does not exist"
                )
            
            # Perform validation checks
            workspace_path = self._get_workspace_path(workspace_name)
            
            checks = [
                ("Workspace directory exists", workspace_path.exists()),
                ("Pipelines directory exists", (workspace_path / "pipelines").exists()),
                ("Templates directory exists", (workspace_path / "templates").exists()),
                ("Configuration file exists", (workspace_path / "config.yaml").exists()),
                ("Storage directory exists", (workspace_path / "storage").exists()),
            ]
            
            passed = sum(1 for _, check in checks if check)
            total = len(checks)
            
            warnings = []
            for check_name, passed_check in checks:
                if not passed_check:
                    warnings.append(f"Failed validation: {check_name}")
            
            success = passed == total
            message = f"Validation passed: {passed}/{total} checks" if success else \
                     f"Validation failed: {passed}/{total} checks passed"
            
            return MigrationResult(
                success=success,
                message=message,
                warnings=warnings
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _workspace_exists(self, name: str) -> bool:
        """Check if workspace exists."""
        if self.workspace_manager:
            return self.workspace_manager.workspace_exists(name)
        return False
    
    def _get_workspace_path(self, name: str) -> Path:
        """Get workspace path."""
        if self.workspace_manager:
            return self.workspace_manager.get_workspace_path(name)
        return Path.home() / ".writeit" / "workspaces" / name


def create_migration_manager(workspace_manager=None) -> MigrationManager:
    """Create migration manager instance."""
    return MigrationManager(workspace_manager)