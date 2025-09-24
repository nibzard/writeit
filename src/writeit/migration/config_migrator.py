# ABOUTME: Configuration migration system for WriteIt
# ABOUTME: Handles migration from legacy configuration formats to new DDD configuration
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import json
import yaml
import shutil
from dataclasses import dataclass, field

from ..domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from ..domains.workspace.value_objects.workspace_name import WorkspaceName
from ..domains.workspace.value_objects.configuration_value import (
    ConfigurationValue,
    StringConfigValue,
    IntConfigValue,
    BoolConfigValue,
    ListConfigValue,
    string_config,
    int_config,
    bool_config,
    list_config
)


@dataclass
class ConfigMigrationResult:
    """Result of a configuration migration."""
    
    success: bool
    message: str
    migrated_keys: int = 0
    skipped_keys: int = 0
    error_keys: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    old_config_path: Optional[Path] = None
    new_config_path: Optional[Path] = None


@dataclass
class LegacyConfigAnalysis:
    """Analysis of legacy configuration."""
    
    config_path: Path
    config_format: str  # "yaml", "json", or "unknown"
    has_valid_config: bool = False
    raw_config_data: Dict[str, Any] = field(default_factory=dict)
    config_errors: List[str] = field(default_factory=list)
    migration_complexity: str = "simple"
    estimated_migrations: int = 0


class ConfigFormatDetector:
    """Detects and analyzes legacy configuration formats."""
    
    @staticmethod
    def detect_config_format(config_path: Path) -> str:
        """Detect configuration file format.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Format type: "yaml", "json", or "unknown"
        """
        if not config_path.exists():
            return "unknown"
        
        # Check file extension
        suffix = config_path.suffix.lower()
        if suffix in ['.yaml', '.yml']:
            return "yaml"
        elif suffix == '.json':
            return "json"
        
        # Try to detect by content
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Read first 1KB
            
            if content.strip().startswith('{'):
                return "json"
            elif ':' in content and not content.strip().startswith('{'):
                return "yaml"
                
        except (OSError, UnicodeDecodeError):
            pass
        
        return "unknown"
    
    @staticmethod
    def analyze_legacy_config(config_path: Path) -> LegacyConfigAnalysis:
        """Analyze legacy configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Analysis results
        """
        analysis = LegacyConfigAnalysis(
            config_path=config_path,
            config_format=ConfigFormatDetector.detect_config_format(config_path)
        )
        
        if not config_path.exists():
            analysis.config_errors.append("Configuration file does not exist")
            return analysis
        
        try:
            # Load configuration data
            if analysis.config_format == "yaml":
                with open(config_path, 'r', encoding='utf-8') as f:
                    analysis.raw_config_data = yaml.safe_load(f) or {}
            elif analysis.config_format == "json":
                with open(config_path, 'r', encoding='utf-8') as f:
                    analysis.raw_config_data = json.load(f) or {}
            else:
                analysis.config_errors.append("Unknown configuration format")
                return analysis
            
            analysis.has_valid_config = True
            
            # Analyze complexity and estimate migrations
            analysis.migration_complexity = ConfigFormatDetector._analyze_complexity(
                analysis.raw_config_data
            )
            analysis.estimated_migrations = len(analysis.raw_config_data)
            
        except (yaml.YAMLError, json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            analysis.config_errors.append(f"Failed to load configuration: {str(e)}")
            analysis.has_valid_config = False
        
        return analysis
    
    @staticmethod
    def _analyze_complexity(config_data: Dict[str, Any]) -> str:
        """Analyze configuration migration complexity."""
        if not config_data:
            return "none"
        
        # Check for complex nested structures
        max_depth = ConfigFormatDetector._get_max_depth(config_data)
        total_keys = ConfigFormatDetector._count_keys(config_data)
        
        if max_depth > 3 or total_keys > 50:
            return "complex"
        elif max_depth > 2 or total_keys > 20:
            return "moderate"
        else:
            return "simple"
    
    @staticmethod
    def _get_max_depth(data: Any, current_depth: int = 0) -> int:
        """Get maximum depth of nested structure."""
        if not isinstance(data, dict):
            return current_depth
        
        if not data:
            return current_depth
        
        return max(
            ConfigFormatDetector._get_max_depth(value, current_depth + 1)
            for value in data.values()
        )
    
    @staticmethod
    def _count_keys(data: Any) -> int:
        """Count total number of keys in nested structure."""
        if not isinstance(data, dict):
            return 0
        
        count = len(data)
        for value in data.values():
            if isinstance(value, dict):
                count += ConfigFormatDetector._count_keys(value)
        
        return count


class ConfigMigrator:
    """Migrates configuration data from legacy to DDD format."""
    
    def __init__(self):
        """Initialize configuration migrator."""
        self.detector = ConfigFormatDetector()
        self.mappings = self._create_config_mappings()
    
    def migrate_config(
        self, 
        legacy_config_path: Path,
        target_config_path: Path,
        backup: bool = True,
        dry_run: bool = False
    ) -> ConfigMigrationResult:
        """Migrate legacy configuration to new DDD format.
        
        Args:
            legacy_config_path: Path to legacy configuration file
            target_config_path: Path for new configuration file
            backup: Whether to create backup of original
            dry_run: Whether to only show what would be done
            
        Returns:
            Migration result
        """
        result = ConfigMigrationResult(
            old_config_path=legacy_config_path,
            new_config_path=target_config_path
        )
        
        try:
            # Analyze legacy configuration
            analysis = self.detector.analyze_legacy_config(legacy_config_path)
            
            if not analysis.has_valid_config:
                result.success = False
                result.message = "Invalid legacy configuration"
                result.errors.extend(analysis.config_errors)
                return result
            
            # Create backup if requested
            if backup and not dry_run:
                backup_path = self._create_config_backup(legacy_config_path)
                result.warnings.append(f"Backup created at: {backup_path}")
            
            # Create new DDD configuration
            new_config = self._create_ddd_config(analysis.raw_config_data)
            
            # Apply legacy config mappings
            migrated_count = 0
            skipped_count = 0
            error_count = 0
            
            for legacy_key, legacy_value in analysis.raw_config_data.items():
                try:
                    migration_result = self._migrate_config_value(
                        legacy_key, legacy_value, new_config
                    )
                    
                    if migration_result is not None:
                        new_config = migration_result
                        migrated_count += 1
                    else:
                        skipped_count += 1
                        result.warnings.append(f"Skipped unmapped config key: {legacy_key}")
                        
                except Exception as e:
                    error_count += 1
                    result.errors.append(f"Failed to migrate {legacy_key}: {str(e)}")
            
            result.migrated_keys = migrated_count
            result.skipped_keys = skipped_count
            result.error_keys = error_count
            
            # Save new configuration
            if not dry_run:
                target_config_path.parent.mkdir(parents=True, exist_ok=True)
                config_data = new_config.to_dict()
                
                with open(target_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            
            result.success = error_count == 0
            result.message = f"Successfully migrated {migrated_count} configuration values" if result.success else \
                           f"Configuration migration completed with {error_count} errors"
            
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"Configuration migration failed: {str(e)}"
            result.errors.append(str(e))
            return result
    
    def _create_config_backup(self, config_path: Path) -> Path:
        """Create backup of configuration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_path.stem}_backup_{timestamp}{config_path.suffix}"
        backup_path = config_path.parent / backup_name
        
        shutil.copy2(config_path, backup_path)
        return backup_path
    
    def _create_ddd_config(self, legacy_data: Dict[str, Any]) -> WorkspaceConfiguration:
        """Create new DDD configuration from legacy data."""
        return WorkspaceConfiguration.default()
    
    def _migrate_config_value(
        self, 
        legacy_key: str, 
        legacy_value: Any, 
        current_config: WorkspaceConfiguration
    ) -> Optional[WorkspaceConfiguration]:
        """Migrate a single configuration value.
        
        Args:
            legacy_key: Legacy configuration key
            legacy_value: Legacy configuration value
            current_config: Current DDD configuration
            
        Returns:
            Updated configuration or None if key should be skipped
        """
        # Find mapping for legacy key
        mapped_key = self.mappings.get(legacy_key)
        if mapped_key is None:
            return None
        
        # Check if the configuration supports this key
        if not current_config.has_key(mapped_key):
            return None
        
        # Type conversion and validation
        try:
            converted_value = self._convert_config_value(mapped_key, legacy_value)
            return current_config.set_value(mapped_key, converted_value)
        except (ValueError, TypeError):
            return None
    
    def _convert_config_value(self, config_key: str, value: Any) -> Any:
        """Convert configuration value to appropriate type."""
        # Get the expected type from the default configuration
        default_config = WorkspaceConfiguration.default()
        
        if not default_config.has_key(config_key):
            raise ValueError(f"Unknown configuration key: {config_key}")
        
        # Get the default value to determine expected type
        default_value = default_config.get_value(config_key)
        
        # Convert based on expected type
        if isinstance(default_value, str):
            return str(value)
        elif isinstance(default_value, bool):
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'on')
            return bool(value)
        elif isinstance(default_value, int):
            return int(value)
        elif isinstance(default_value, list):
            if isinstance(value, str):
                # Split comma-separated strings
                return [item.strip() for item in value.split(',') if item.strip()]
            elif isinstance(value, list):
                return [str(item) for item in value]
            else:
                return [str(value)]
        else:
            return str(value)
    
    def _create_config_mappings(self) -> Dict[str, str]:
        """Create mapping from legacy config keys to new DDD keys."""
        return {
            # Legacy workspace config mappings
            "default_pipeline": "default_pipeline",
            "default_model": "default_model",
            "model": "default_model",
            "openai_api_key": "openai_api_key",  # Will be stored securely
            "anthropic_api_key": "anthropic_api_key",  # Will be stored securely
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "cache_enabled": "enable_cache",
            "cache_ttl": "cache_ttl_hours",
            "parallel_execution": "parallel_execution",
            "max_parallel": "max_parallel_steps",
            "retry_count": "retry_attempts",
            "output_format": "output_format",
            "log_level": "log_level",
            
            # Legacy LLM provider configs
            "llm_providers": "llm_providers",  # Special handling needed
            
            # Template settings
            "template_paths": "template_search_paths",
            "auto_validate": "auto_validate_templates",
            
            # Additional legacy mappings
            "workspace_name": "workspace_name",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }


class ConfigMigrationManager:
    """High-level configuration migration manager."""
    
    def __init__(self):
        """Initialize configuration migration manager."""
        self.migrator = ConfigMigrator()
        self.detector = ConfigFormatDetector()
    
    def migrate_workspace_configs(
        self, 
        workspace_path: Path,
        backup: bool = True,
        dry_run: bool = False
    ) -> List[ConfigMigrationResult]:
        """Migrate all configuration files in a workspace.
        
        Args:
            workspace_path: Path to workspace directory
            backup: Whether to create backups
            dry_run: Whether to only show what would be done
            
        Returns:
            List of migration results
        """
        results = []
        
        # Look for legacy configuration files
        config_files = [
            workspace_path / ".writeit" / "config.yaml",
            workspace_path / ".writeit" / "config.yml",
            workspace_path / ".writeit" / "config.json",
            workspace_path / "workspace.yaml",
            workspace_path / "workspace.yml",
            workspace_path / "config.yaml",
            workspace_path / "config.yml",
            workspace_path / "config.json",
        ]
        
        target_config_path = workspace_path / "config.yaml"
        
        for config_file in config_files:
            if config_file.exists():
                result = self.migrator.migrate_config(
                    config_file,
                    target_config_path,
                    backup=backup,
                    dry_run=dry_run
                )
                results.append(result)
                
                # Stop after first successful migration to avoid conflicts
                if result.success:
                    break
        
        return results
    
    def validate_migrated_config(self, config_path: Path) -> ConfigMigrationResult:
        """Validate that a migrated configuration is working correctly.
        
        Args:
            config_path: Path to migrated configuration file
            
        Returns:
            Validation result
        """
        result = ConfigMigrationResult(
            new_config_path=config_path
        )
        
        try:
            if not config_path.exists():
                result.success = False
                result.message = "Configuration file does not exist"
                return result
            
            # Try to load the configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Create DDD configuration from loaded data
            try:
                config = WorkspaceConfiguration.from_dict(config_data)
                result.success = True
                result.message = "Configuration validation passed"
                result.migrated_keys = len(config_data)
                
                # Check for required keys
                required_keys = [
                    "default_model",
                    "max_tokens", 
                    "temperature",
                    "enable_cache"
                ]
                
                for key in required_keys:
                    if not config.has_key(key):
                        result.warnings.append(f"Missing recommended configuration key: {key}")
                
            except Exception as e:
                result.success = False
                result.message = f"Configuration validation failed: {str(e)}"
                result.errors.append(str(e))
            
        except Exception as e:
            result.success = False
            result.message = f"Failed to validate configuration: {str(e)}"
            result.errors.append(str(e))
        
        return result
    
    def analyze_config_migration_needs(self, workspace_path: Path) -> List[LegacyConfigAnalysis]:
        """Analyze configuration migration needs for a workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            List of configuration analyses
        """
        analyses = []
        
        config_files = [
            workspace_path / ".writeit" / "config.yaml",
            workspace_path / ".writeit" / "config.yml", 
            workspace_path / ".writeit" / "config.json",
            workspace_path / "workspace.yaml",
            workspace_path / "workspace.yml",
            workspace_path / "config.yaml",
            workspace_path / "config.yml",
            workspace_path / "config.json",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                analysis = self.detector.analyze_legacy_config(config_file)
                analyses.append(analysis)
        
        return analyses


def create_config_migration_manager() -> ConfigMigrationManager:
    """Create configuration migration manager instance."""
    return ConfigMigrationManager()