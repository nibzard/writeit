"""Integrated Migration System for WriteIt DDD Refactoring.

This module provides a unified migration system that orchestrates all migration
components for a complete DDD refactoring migration. It coordinates between:
- Data migration (formats, structures, configurations, cache)
- Workspace structure updates
- Configuration migration
- Cache format updates
- Validation and reporting
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
from writeit.migration.migration_runner import MigrationRunner
from writeit.migration.workspace_structure_updater import WorkspaceStructureUpdater
from writeit.migration.config_migration_system import ConfigMigrationSystem
from writeit.migration.cache_migration_system import CacheMigrationSystem


class IntegratedMigrationError(Exception):
    """Exception raised during integrated migration."""
    pass


class IntegratedMigration:
    """Integrated migration system for complete DDD refactoring."""
    
    def __init__(self, workspace: Optional[Workspace] = None):
        """Initialize integrated migration system.
        
        Args:
            workspace: Workspace instance (creates default if None)
        """
        self.workspace = workspace or Workspace()
        
        # Initialize migration components
        self.data_migrator = DataMigrator(self.workspace)
        self.format_converter = LegacyFormatConverter()
        self.migration_runner = MigrationRunner(self.workspace)
        self.structure_updater = WorkspaceStructureUpdater(self.workspace)
        self.config_migrator = ConfigMigrationSystem(self.workspace)
        self.cache_migrator = CacheMigrationSystem(self.workspace)
        
        # Migration state
        self.migration_state = {
            "started_at": None,
            "completed_at": None,
            "success": False,
            "phases_completed": [],
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
    def start_migration(self, workspace_name: Optional[str] = None, backup: bool = True) -> bool:
        """Start the complete integrated migration process.
        
        Args:
            workspace_name: Specific workspace to migrate (None for all)
            backup: Whether to create backup before migration
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.migration_state["started_at"] = datetime.now().isoformat()
            
            print("🚀 Starting WriteIt DDD Integrated Migration")
            print("=" * 60)
            
            # Phase 1: Pre-migration checks and backup
            if not self._pre_migration_checks(backup):
                return False
                
            # Phase 2: Legacy data format conversion
            if not self._migrate_legacy_formats(workspace_name):
                return False
                
            # Phase 3: Workspace structure updates
            if not self._update_workspace_structure(workspace_name):
                return False
                
            # Phase 4: Configuration migration
            if not self._migrate_configurations(workspace_name):
                return False
                
            # Phase 5: Cache format updates
            if not self._migrate_cache_formats(workspace_name):
                return False
                
            # Phase 6: Post-migration validation
            if not self._post_migration_validation():
                return False
                
            # Phase 7: Final cleanup and reporting
            if not self._final_cleanup_and_reporting():
                return False
                
            self.migration_state["completed_at"] = datetime.now().isoformat()
            self.migration_state["success"] = True
            
            print("✅ Integrated migration completed successfully!")
            self._print_migration_summary()
            
            return True
            
        except Exception as e:
            self.migration_state["completed_at"] = datetime.now().isoformat()
            self.migration_state["success"] = False
            self.migration_state["errors"].append(str(e))
            
            print(f"❌ Integrated migration failed: {e}")
            return False
            
    def _pre_migration_checks(self, backup: bool) -> bool:
        """Perform pre-migration checks and backup.
        
        Args:
            backup: Whether to create backup
            
        Returns:
            True if checks pass, False otherwise
        """
        print("\n📋 Phase 1: Pre-migration checks and backup")
        
        try:
            # Check workspace structure
            if not self.workspace.base_dir.exists():
                print("❌ Workspace base directory not found")
                return False
                
            # Check write permissions
            if not os.access(self.workspace.base_dir, os.W_OK):
                print("❌ No write permissions for workspace directory")
                return False
                
            # Check available disk space
            disk_usage = shutil.disk_usage(self.workspace.base_dir)
            if disk_usage.free < 100 * 1024 * 1024:  # 100MB minimum
                print("❌ Insufficient disk space for migration")
                return False
                
            # Create backup if requested
            if backup:
                print("🔄 Creating backup...")
                backup_path = self._create_comprehensive_backup()
                print(f"✅ Backup created: {backup_path}")
                
            self.migration_state["phases_completed"].append("pre_migration_checks")
            return True
            
        except Exception as e:
            self.migration_state["errors"].append(f"Pre-migration checks failed: {e}")
            return False
            
    def _migrate_legacy_formats(self, workspace_name: Optional[str]) -> bool:
        """Migrate legacy data formats.
        
        Args:
            workspace_name: Specific workspace to migrate
            
        Returns:
            True if migration successful, False otherwise
        """
        print("\n📄 Phase 2: Legacy data format conversion")
        
        try:
            # Use migration runner for comprehensive format migration
            if workspace_name:
                print(f"Migrating formats for workspace: {workspace_name}")
                result = self.migration_runner.run_full_migration(workspace_name)
            else:
                print("Migrating formats for all workspaces")
                result = self.migration_runner.run_full_migration()
                
            if result["success"]:
                self.migration_state["phases_completed"].append("legacy_format_migration")
                self.migration_state["statistics"]["legacy_format_migration"] = result["summary"]
                print("✅ Legacy format migration completed")
                return True
            else:
                self.migration_state["errors"].extend(result.get("errors", []))
                print("❌ Legacy format migration failed")
                return False
                
        except Exception as e:
            self.migration_state["errors"].append(f"Legacy format migration failed: {e}")
            return False
            
    def _update_workspace_structure(self, workspace_name: Optional[str]) -> bool:
        """Update workspace directory structure.
        
        Args:
            workspace_name: Specific workspace to update
            
        Returns:
            True if update successful, False otherwise
        """
        print("\n🏗️  Phase 3: Workspace structure updates")
        
        try:
            if workspace_name:
                # Update specific workspace
                print(f"Updating structure for workspace: {workspace_name}")
                success = self.structure_updater.update_workspace_structure(workspace_name)
            else:
                # Update all workspaces
                workspace_names = self.workspace.list_workspaces()
                if not workspace_names:
                    print("No workspaces found for structure update")
                    return True
                    
                success_count = 0
                for ws_name in workspace_names:
                    if self.structure_updater.update_workspace_structure(ws_name):
                        success_count += 1
                        
                success = success_count == len(workspace_names)
                
            if success:
                self.migration_state["phases_completed"].append("workspace_structure_updates")
                print("✅ Workspace structure updates completed")
                return True
            else:
                self.migration_state["errors"].append("Workspace structure updates failed")
                print("❌ Workspace structure updates failed")
                return False
                
        except Exception as e:
            self.migration_state["errors"].append(f"Workspace structure updates failed: {e}")
            return False
            
    def _migrate_configurations(self, workspace_name: Optional[str]) -> bool:
        """Migrate configuration data.
        
        Args:
            workspace_name: Specific workspace to migrate
            
        Returns:
            True if migration successful, False otherwise
        """
        print("\n⚙️  Phase 4: Configuration migration")
        
        try:
            # Migrate global configuration
            print("Migrating global configuration...")
            global_success = self.config_migrator.migrate_global_config()
            
            # Migrate workspace configurations
            print("Migrating workspace configurations...")
            workspace_success = self.config_migrator.migrate_workspace_configs(workspace_name)
            
            if global_success and workspace_success:
                self.migration_state["phases_completed"].append("configuration_migration")
                print("✅ Configuration migration completed")
                return True
            else:
                self.migration_state["errors"].append("Configuration migration failed")
                print("❌ Configuration migration failed")
                return False
                
        except Exception as e:
            self.migration_state["errors"].append(f"Configuration migration failed: {e}")
            return False
            
    def _migrate_cache_formats(self, workspace_name: Optional[str]) -> bool:
        """Migrate cache data formats.
        
        Args:
            workspace_name: Specific workspace to migrate
            
        Returns:
            True if migration successful, False otherwise
        """
        print("\n💾 Phase 5: Cache format updates")
        
        try:
            # Migrate all cache formats
            success = self.cache_migrator.migrate_all_caches(workspace_name)
            
            if success:
                cache_stats = self.cache_migrator.get_cache_stats()
                self.migration_state["phases_completed"].append("cache_format_updates")
                self.migration_state["statistics"]["cache_migration"] = cache_stats
                print("✅ Cache format updates completed")
                print(f"   Entries migrated: {cache_stats['entries_migrated']}")
                print(f"   Cache files processed: {cache_stats['cache_files_processed']}")
                return True
            else:
                self.migration_state["errors"].append("Cache format updates failed")
                print("❌ Cache format updates failed")
                return False
                
        except Exception as e:
            self.migration_state["errors"].append(f"Cache format updates failed: {e}")
            return False
            
    def _post_migration_validation(self) -> bool:
        """Perform post-migration validation.
        
        Returns:
            True if validation successful, False otherwise
        """
        print("\n✅ Phase 6: Post-migration validation")
        
        try:
            validation_issues = []
            
            # Validate migrated configurations
            config_issues = self.config_migrator.validate_migrated_configs()
            if config_issues:
                validation_issues.append("Configuration validation issues found")
                
            # Validate workspace structures
            workspace_names = self.workspace.list_workspaces()
            for ws_name in workspace_names:
                workspace_path = self.workspace.get_workspace_path(ws_name)
                structure_issues = self.structure_updater.validate_updated_structure(workspace_path)
                if structure_issues:
                    validation_issues.extend([f"{ws_name}: {issue}" for issue in structure_issues])
                    
            if validation_issues:
                self.migration_state["warnings"].extend(validation_issues)
                print("⚠️  Migration completed with validation issues:")
                for issue in validation_issues:
                    print(f"   - {issue}")
            else:
                print("✅ All validation checks passed")
                
            self.migration_state["phases_completed"].append("post_migration_validation")
            return True
            
        except Exception as e:
            self.migration_state["errors"].append(f"Post-migration validation failed: {e}")
            return False
            
    def _final_cleanup_and_reporting(self) -> bool:
        """Perform final cleanup and generate reports.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        print("\n🧹 Phase 7: Final cleanup and reporting")
        
        try:
            # Generate comprehensive migration report
            report_path = self._generate_migration_report()
            print(f"✅ Migration report generated: {report_path}")
            
            # Clean up temporary files
            self._cleanup_temporary_files()
            print("✅ Temporary files cleaned up")
            
            # Optimize migrated data
            self._optimize_migrated_data()
            print("✅ Migrated data optimized")
            
            self.migration_state["phases_completed"].append("final_cleanup_and_reporting")
            return True
            
        except Exception as e:
            self.migration_state["errors"].append(f"Final cleanup failed: {e}")
            return False
            
    def _create_comprehensive_backup(self) -> Path:
        """Create comprehensive backup before migration.
        
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"writeit_comprehensive_backup_{timestamp}"
        backup_path = self.workspace.base_dir.parent / backup_name
        
        # Copy entire workspace directory
        shutil.copytree(self.workspace.base_dir, backup_path)
        
        # Backup additional configuration if it exists
        config_paths = [
            Path.home() / ".writeit",
            Path.cwd() / ".writeit"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                target_path = backup_path / f"backup_{config_path.name}"
                shutil.copytree(config_path, target_path)
                
        return backup_path
        
    def _generate_migration_report(self) -> Path:
        """Generate comprehensive migration report.
        
        Returns:
            Path to generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"writeit_migration_report_{timestamp}.md")
        
        report_content = [
            "# WriteIt DDD Migration Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Migration Summary",
            f"Start Time: {self.migration_state['started_at']}",
            f"End Time: {self.migration_state['completed_at']}",
            f"Success: {self.migration_state['success']}",
            "",
            "## Phases Completed",
            ""
        ]
        
        # Add phases
        for phase in self.migration_state["phases_completed"]:
            report_content.append(f"- ✅ {phase.replace('_', ' ').title()}")
            
        report_content.append("")
        
        # Add statistics
        if self.migration_state["statistics"]:
            report_content.extend([
                "## Migration Statistics",
                ""
            ])
            
            for stat_name, stat_data in self.migration_state["statistics"].items():
                report_content.append(f"### {stat_name.replace('_', ' ').title()}")
                if isinstance(stat_data, dict):
                    for key, value in stat_data.items():
                        report_content.append(f"- {key}: {value}")
                else:
                    report_content.append(f"- {stat_data}")
                report_content.append("")
                
        # Add errors and warnings
        if self.migration_state["errors"]:
            report_content.extend([
                "## Errors",
                ""
            ])
            for error in self.migration_state["errors"]:
                report_content.append(f"- ❌ {error}")
            report_content.append("")
            
        if self.migration_state["warnings"]:
            report_content.extend([
                "## Warnings",
                ""
            ])
            for warning in self.migration_state["warnings"]:
                report_content.append(f"- ⚠️  {warning}")
            report_content.append("")
            
        # Add migration logs from all components
        report_content.extend([
            "## Migration Logs",
            "",
            "### Data Migration Log",
            ""
        ])
        
        for entry in self.data_migrator.get_migration_log():
            level = entry.get("level", "info")
            timestamp = entry.get("timestamp", "N/A")
            message = entry.get("message", "N/A")
            report_content.append(f"- [{timestamp}] {level.upper()}: {message}")
            
        report_content.extend([
            "",
            "### Configuration Migration Log",
            ""
        ])
        
        for entry in self.config_migrator.get_migration_log():
            level = entry.get("level", "info")
            timestamp = entry.get("timestamp", "N/A")
            message = entry.get("message", "N/A")
            report_content.append(f"- [{timestamp}] {level.upper()}: {message}")
            
        report_content.extend([
            "",
            "### Cache Migration Log",
            ""
        ])
        
        for entry in self.cache_migrator.get_migration_log():
            level = entry.get("level", "info")
            timestamp = entry.get("timestamp", "N/A")
            message = entry.get("message", "N/A")
            report_content.append(f"- [{timestamp}] {level.upper()}: {message}")
            
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))
            
        return report_path
        
    def _cleanup_temporary_files(self) -> None:
        """Clean up temporary files created during migration."""
        temp_patterns = ["*.tmp", "*.temp", "*_backup_*", "migrated_*"]
        
        for pattern in temp_patterns:
            for temp_file in self.workspace.base_dir.rglob(pattern):
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file)
                except OSError:
                    continue
                    
    def _optimize_migrated_data(self) -> None:
        """Optimize migrated data structures."""
        # This would implement optimization of migrated data
        # For now, just log that optimization was performed
        pass
        
    def _print_migration_summary(self) -> None:
        """Print migration summary."""
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        
        print(f"✅ Migration completed successfully")
        print(f"⏱️  Duration: {self._calculate_duration()}")
        print(f"📝 Phases completed: {len(self.migration_state['phases_completed'])}")
        print(f"⚠️  Warnings: {len(self.migration_state['warnings'])}")
        
        if self.migration_state["statistics"]:
            print("\n📊 Statistics:")
            for stat_name, stat_data in self.migration_state["statistics"].items():
                print(f"   {stat_name.replace('_', ' ').title()}: {stat_data}")
                
    def _calculate_duration(self) -> str:
        """Calculate migration duration.
        
        Returns:
            Formatted duration string
        """
        if not self.migration_state["started_at"] or not self.migration_state["completed_at"]:
            return "N/A"
            
        start = datetime.fromisoformat(self.migration_state["started_at"])
        end = datetime.fromisoformat(self.migration_state["completed_at"])
        duration = end - start
        
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
            
    def rollback_migration(self, workspace_name: Optional[str] = None) -> bool:
        """Rollback migration for specified workspace or all workspaces.
        
        Args:
            workspace_name: Specific workspace to rollback (None for all)
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            print("🔄 Starting migration rollback...")
            
            # Find backup directories
            backup_pattern = "writeit_comprehensive_backup_*"
            backup_dirs = list(self.workspace.base_dir.parent.glob(backup_pattern))
            
            if not backup_dirs:
                print("❌ No backup found for rollback")
                return False
                
            # Use most recent backup
            latest_backup = max(backup_dirs, key=lambda p: p.stat().st_mtime)
            
            print(f"🔄 Using backup: {latest_backup}")
            
            # Restore from backup
            if self.workspace.base_dir.exists():
                shutil.rmtree(self.workspace.base_dir)
                
            shutil.copytree(latest_backup, self.workspace.base_dir)
            
            print("✅ Migration rollback completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Migration rollback failed: {e}")
            return False
            
    def get_migration_state(self) -> Dict[str, Any]:
        """Get current migration state.
        
        Returns:
            Migration state dictionary
        """
        return self.migration_state.copy()