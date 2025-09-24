# ABOUTME: Migration validation utilities for WriteIt DDD refactoring
# ABOUTME: Provides comprehensive validation of migration completeness and correctness
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import json
import yaml
from dataclasses import dataclass, field


@dataclass
class MigrationValidationResult:
    """Result of migration validation."""
    
    success: bool
    message: str
    workspace_name: str
    validation_checks: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    migration_score: float = 0.0


class MigrationValidator:
    """Comprehensive migration validator for WriteIt DDD refactoring."""
    
    def __init__(self):
        """Initialize migration validator."""
        self.validation_log = []
    
    def log_validation(self, message: str, level: str = "info") -> None:
        """Log validation activity."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.validation_log.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
    
    def validate_complete_migration(
        self, 
        workspace_path: Path,
        workspace_name: str
    ) -> MigrationValidationResult:
        """Perform comprehensive migration validation.
        
        Args:
            workspace_path: Path to workspace directory
            workspace_name: Name of workspace
            
        Returns:
            Comprehensive validation result
        """
        result = MigrationValidationResult(
            success=False,
            message="Migration validation in progress",
            workspace_name=workspace_name
        )
        
        try:
            self.log_validation(f"Starting comprehensive migration validation for: {workspace_name}")
            
            # Run all validation checks
            checks = {
                "workspace_structure": self._validate_workspace_structure(workspace_path),
                "ddd_compatibility": self._validate_ddd_compatibility(workspace_path),
                "configuration_migration": self._validate_configuration_migration(workspace_path),
                "cache_format": self._validate_cache_format(workspace_path),
                "data_integrity": self._validate_data_integrity(workspace_path),
                "legacy_cleanup": self._validate_legacy_cleanup(workspace_path),
                "metadata_completeness": self._validate_metadata_completeness(workspace_path)
            }
            
            result.validation_checks = checks
            
            # Calculate migration score
            passed_checks = sum(1 for check in checks.values() if check)
            total_checks = len(checks)
            result.migration_score = (passed_checks / total_checks) * 100.0
            
            # Generate recommendations
            result.recommendations = self._generate_recommendations(checks, workspace_path)
            
            # Determine overall success
            critical_checks = [
                "workspace_structure",
                "ddd_compatibility", 
                "configuration_migration",
                "data_integrity"
            ]
            
            critical_passed = all(checks.get(check, False) for check in critical_checks)
            result.success = critical_passed and result.migration_score >= 80.0
            
            # Generate message
            if result.success:
                result.message = (
                    f"Migration validation passed for {workspace_name} "
                    f"({result.migration_score:.1f}% complete)"
                )
            else:
                failed_critical = [check for check in critical_checks if not checks.get(check, False)]
                result.message = (
                    f"Migration validation failed for {workspace_name} "
                    f"({result.migration_score:.1f}% complete). "
                    f"Failed critical checks: {', '.join(failed_critical)}"
                )
            
            # Collect warnings and errors
            if result.migration_score < 100.0:
                result.warnings.append(f"Migration is {100.0 - result.migration_score:.1f}% incomplete")
            
            if not result.success:
                result.errors.append("Critical migration checks failed")
            
            self.log_validation(f"Validation completed: {result.migration_score:.1f}% complete")
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"Migration validation failed: {str(e)}"
            result.errors.append(str(e))
            return result
    
    def _validate_workspace_structure(self, workspace_path: Path) -> bool:
        """Validate workspace directory structure."""
        self.log_validation("Validating workspace structure...")
        
        required_dirs = [
            "pipelines",
            "templates", 
            "cache",
            "storage",
            "config.yaml"
        ]
        
        missing_items = []
        
        # Check required directories
        for dir_name in ["pipelines", "templates", "cache", "storage"]:
            dir_path = workspace_path / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                missing_items.append(f"directory: {dir_name}")
        
        # Check config file
        config_file = workspace_path / "config.yaml"
        if not config_file.exists():
            missing_items.append("file: config.yaml")
        
        if missing_items:
            self.log_validation(f"Missing workspace structure items: {', '.join(missing_items)}", "warning")
            return False
        
        self.log_validation("Workspace structure validation passed")
        return True
    
    def _validate_ddd_compatibility(self, workspace_path: Path) -> bool:
        """Validate DDD compatibility markers."""
        self.log_validation("Validating DDD compatibility...")
        
        config_file = workspace_path / "config.yaml"
        if not config_file.exists():
            self.log_validation("No config file found for DDD validation", "warning")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Check for DDD compatibility markers
            ddd_markers = [
                ("structure_version", "2.0"),
                ("ddd_compatible", True),
                ("workspace_isolated", True)
            ]
            
            missing_markers = []
            for marker, expected_value in ddd_markers:
                if config.get(marker) != expected_value:
                    missing_markers.append(f"{marker}: {expected_value}")
            
            if missing_markers:
                self.log_validation(f"Missing DDD compatibility markers: {', '.join(missing_markers)}", "warning")
                return False
            
            self.log_validation("DDD compatibility validation passed")
            return True
            
        except Exception as e:
            self.log_validation(f"DDD compatibility validation error: {e}", "error")
            return False
    
    def _validate_configuration_migration(self, workspace_path: Path) -> bool:
        """Validate configuration migration."""
        self.log_validation("Validating configuration migration...")
        
        config_file = workspace_path / "config.yaml"
        if not config_file.exists():
            self.log_validation("No configuration file found", "warning")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Check for migrated configuration structure
            required_config_keys = [
                "version",
                "workspace_name", 
                "settings",
                "llm_providers"
            ]
            
            missing_keys = [key for key in required_config_keys if key not in config]
            if missing_keys:
                self.log_validation(f"Missing configuration keys: {', '.join(missing_keys)}", "warning")
                return False
            
            # Check settings structure
            settings = config.get("settings", {})
            required_settings = ["default_model", "auto_save", "max_history"]
            missing_settings = [key for key in required_settings if key not in settings]
            if missing_settings:
                self.log_validation(f"Missing settings: {', '.join(missing_settings)}", "warning")
                return False
            
            self.log_validation("Configuration migration validation passed")
            return True
            
        except Exception as e:
            self.log_validation(f"Configuration migration validation error: {e}", "error")
            return False
    
    def _validate_cache_format(self, workspace_path: Path) -> bool:
        """Validate cache format migration."""
        self.log_validation("Validating cache format...")
        
        cache_dir = workspace_path / "cache"
        if not cache_dir.exists():
            self.log_validation("No cache directory found", "info")
            return True  # Cache is optional
        
        try:
            # Check cache metadata
            metadata_file = cache_dir / "cache_metadata.json"
            if not metadata_file.exists():
                self.log_validation("Cache metadata file missing", "warning")
                return False
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check cache format version
            if metadata.get("cache_version") != "2.0":
                self.log_validation("Cache format version not updated", "warning")
                return False
            
            # Check domain directories
            domain_dirs = ["llm", "pipeline", "workspace", "temp"]
            for domain_dir in domain_dirs:
                dir_path = cache_dir / domain_dir
                if not dir_path.exists():
                    self.log_validation(f"Missing domain cache directory: {domain_dir}", "warning")
                    return False
            
            # Check cache entries format
            cache_files = list(cache_dir.glob("*.json"))
            for cache_file in cache_files:
                if cache_file.name == "cache_metadata.json":
                    continue
                
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    if isinstance(cache_data, dict):
                        if not cache_data.get("workspace_isolated"):
                            self.log_validation(f"Cache entry not workspace isolated: {cache_file.name}", "warning")
                            return False
                except Exception:
                    continue
            
            self.log_validation("Cache format validation passed")
            return True
            
        except Exception as e:
            self.log_validation(f"Cache format validation error: {e}", "error")
            return False
    
    def _validate_data_integrity(self, workspace_path: Path) -> bool:
        """Validate data integrity after migration."""
        self.log_validation("Validating data integrity...")
        
        integrity_issues = []
        
        # Check pipeline templates
        templates_dir = workspace_path / "templates"
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.yaml"):
                try:
                    with open(template_file, 'r') as f:
                        template_data = yaml.safe_load(f)
                    
                    if not template_data or "metadata" not in template_data:
                        integrity_issues.append(f"Invalid template structure: {template_file.name}")
                except Exception as e:
                    integrity_issues.append(f"Cannot read template {template_file.name}: {e}")
        
        # Check configuration integrity
        config_file = workspace_path / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                if not isinstance(config, dict):
                    integrity_issues.append("Configuration is not a valid dictionary")
            except Exception as e:
                integrity_issues.append(f"Cannot read configuration: {e}")
        
        if integrity_issues:
            for issue in integrity_issues:
                self.log_validation(f"Data integrity issue: {issue}", "warning")
            return False
        
        self.log_validation("Data integrity validation passed")
        return True
    
    def _validate_legacy_cleanup(self, workspace_path: Path) -> bool:
        """Validate legacy file cleanup."""
        self.log_validation("Validating legacy cleanup...")
        
        legacy_items = [
            ".writeit",
            "workspace.yaml",
            "config.json"
        ]
        
        found_legacy = []
        
        for item in legacy_items:
            item_path = workspace_path / item
            if item_path.exists():
                found_legacy.append(item)
        
        if found_legacy:
            self.log_validation(f"Found legacy items: {', '.join(found_legacy)}", "warning")
            return False
        
        self.log_validation("Legacy cleanup validation passed")
        return True
    
    def _validate_metadata_completeness(self, workspace_path: Path) -> bool:
        """Validate metadata completeness."""
        self.log_validation("Validating metadata completeness...")
        
        config_file = workspace_path / "config.yaml"
        if not config_file.exists():
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Check required metadata
            required_metadata = [
                "created_at",
                "updated_at",
                "version"
            ]
            
            missing_metadata = [key for key in required_metadata if key not in config]
            if missing_metadata:
                self.log_validation(f"Missing metadata: {', '.join(missing_metadata)}", "warning")
                return False
            
            # Check migration metadata
            migration_metadata = config.get("migration_metadata", {})
            if migration_metadata:
                required_migration_meta = ["migrated_at", "migration_version"]
                missing_migration = [key for key in required_migration_meta if key not in migration_metadata]
                if missing_migration:
                    self.log_validation(f"Missing migration metadata: {', '.join(missing_migration)}", "warning")
                    return False
            
            self.log_validation("Metadata completeness validation passed")
            return True
            
        except Exception as e:
            self.log_validation(f"Metadata validation error: {e}", "error")
            return False
    
    def _generate_recommendations(
        self, 
        checks: Dict[str, bool], 
        workspace_path: Path
    ) -> List[str]:
        """Generate improvement recommendations.
        
        Args:
            checks: Validation check results
            workspace_path: Path to workspace
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Structure recommendations
        if not checks.get("workspace_structure", False):
            recommendations.append("Run workspace structure migration: writeit migrate structure <workspace_name>")
        
        # Configuration recommendations
        if not checks.get("configuration_migration", False):
            recommendations.append("Run configuration migration: writeit migrate workspace <workspace_name>")
        
        # Cache recommendations
        if not checks.get("cache_format", False):
            recommendations.append("Run cache format migration: writeit migrate cache <workspace_name>")
        
        # DDD compatibility recommendations
        if not checks.get("ddd_compatibility", False):
            recommendations.append("Update configuration for DDD compatibility")
        
        # Cleanup recommendations
        if not checks.get("legacy_cleanup", False):
            recommendations.append("Clean up legacy files after successful migration")
        
        # General recommendations
        if checks.get("workspace_structure", False) and checks.get("configuration_migration", False):
            recommendations.append("Run full migration validation: writeit migrate validate <workspace_name>")
        
        return recommendations
    
    def generate_validation_report(self, result: MigrationValidationResult) -> str:
        """Generate detailed validation report.
        
        Args:
            result: Validation result
            
        Returns:
            Formatted validation report
        """
        report = [
            "# WriteIt Migration Validation Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Workspace: {result.workspace_name}",
            "",
            "## Summary",
            f"- Overall Status: {'✅ PASSED' if result.success else '❌ FAILED'}",
            f"- Migration Score: {result.migration_score:.1f}%",
            f"- Message: {result.message}",
            "",
            "## Validation Checks",
            ""
        ]
        
        # Add check results
        for check_name, passed in result.validation_checks.items():
            status = "✅" if passed else "❌"
            report.append(f"- {status} {check_name.replace('_', ' ').title()}")
        
        report.append("")
        
        # Add warnings
        if result.warnings:
            report.append("## Warnings")
            for warning in result.warnings:
                report.append(f"- {warning}")
            report.append("")
        
        # Add errors
        if result.errors:
            report.append("## Errors")
            for error in result.errors:
                report.append(f"- {error}")
            report.append("")
        
        # Add recommendations
        if result.recommendations:
            report.append("## Recommendations")
            for recommendation in result.recommendations:
                report.append(f"- {recommendation}")
            report.append("")
        
        # Add next steps
        if result.success:
            report.append("## Next Steps")
            report.append("- Migration is complete and validated")
            report.append("- You can safely use the workspace with the new DDD structure")
        else:
            report.append("## Next Steps")
            report.append("- Address the failed validation checks")
            report.append("- Run the recommended migration commands")
            report.append("- Re-run validation after fixes")
        
        return "\n".join(report)


def create_migration_validator() -> MigrationValidator:
    """Create migration validator instance."""
    return MigrationValidator()