"""Command-line interface for WriteIt data migration.

This module provides CLI commands for migrating existing WriteIt data
from legacy formats to the new DDD-based structure.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.migration.data_migrator import MigrationManager, create_migration_manager
from writeit.migration.workspace_structure_updater import WorkspaceStructureUpdater
from writeit.migration.cache_migrator import create_cache_migration_manager
from writeit.migration.cache_format_updater import create_cache_format_updater
from writeit.migration.migration_validator import create_migration_validator


def migrate_workspace(args):
    """Migrate a single workspace."""
    try:
        # Initialize workspace and migration manager
        workspace = Workspace()
        migration_manager = create_migration_manager(workspace)
        
        # Get workspace path
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
            
        # Run migration
        if args.dry_run:
            print(f"DRY RUN: Would migrate workspace {workspace_name}")
            legacy_data = migration_manager.detector.analyze_legacy_workspace(workspace_path)
            print(f"  - Pipelines: {legacy_data.pipeline_count}")
            print(f"  - Articles: {legacy_data.article_count}")
            print(f"  - Has LMDB data: {legacy_data.has_lmdb}")
            return 0
            
        result = migration_manager.migrator.migrate_workspace(
            workspace_path,
            backup=True,
            overwrite=False
        )
        
        if result.success:
            print(f"✅ Successfully migrated workspace: {workspace_name}")
            print(f"   - Migrated {result.migrated_items} items")
            if result.warnings:
                print(f"   - {len(result.warnings)} warnings")
            if result.backup_path:
                print(f"   - Backup: {result.backup_path}")
                
            # Validate migration
            validation_result = migration_manager.validate_migration(workspace_name)
            if validation_result.success:
                print(f"✅ Migration validation passed")
            else:
                print(f"⚠️  Migration validation issues: {len(validation_result.warnings)} warnings")
                for warning in validation_result.warnings:
                    print(f"     - {warning}")
                
            return 0
        else:
            print(f"❌ Migration failed for workspace: {workspace_name}")
            print(f"   - {result.message}")
            if result.errors:
                for error in result.errors:
                    print(f"     - {error}")
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1


def migrate_all_workspaces(args):
    """Migrate all available workspaces."""
    try:
        # Initialize workspace and migration manager
        workspace = Workspace()
        migration_manager = create_migration_manager(workspace)
        
        # Scan for legacy workspaces
        legacy_workspaces = migration_manager.scan_for_migrations()
        
        if not legacy_workspaces:
            print("No legacy workspaces found to migrate")
            return 0
            
        print(f"Found {len(legacy_workspaces)} workspaces to migrate")
        
        # Migrate each workspace
        results = migration_manager.migrate_all(
            interactive=not args.batch,
            backup=True
        )
        
        # Calculate summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        skipped = sum(1 for r in results if not r.success and "Skipped" in r.message)
        
        print(f"\n📊 Migration Summary:")
        print(f"   Total workspaces: {len(results)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Skipped: {skipped}")
        
        if args.verbose:
            for result in results:
                status = "✅" if result.success else "❌"
                print(f"   {status} {result.message}")
                if result.warnings:
                    for warning in result.warnings:
                        print(f"      ⚠️  {warning}")
                if result.errors:
                    for error in result.errors:
                        print(f"      💥 {error}")
        
        return 0 if failed == 0 else 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1


def validate_migration(args):
    """Validate migrated workspaces."""
    try:
        # Initialize workspace and migration manager
        workspace = Workspace()
        migration_manager = create_migration_manager(workspace)
        
        # Get workspace to validate
        workspace_name = args.workspace_name
        
        # Validate migration
        result = migration_manager.validate_migration(workspace_name)
        
        if result.success:
            print(f"✅ Migration validation passed for {workspace_name}")
            if result.warnings:
                print(f"   {len(result.warnings)} warnings:")
                for warning in result.warnings:
                    print(f"     - {warning}")
            return 0
        else:
            print(f"❌ Migration validation failed for {workspace_name}:")
            print(f"   - {result.message}")
            if result.errors:
                for error in result.errors:
                    print(f"     - {error}")
            return 1
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return 1


def backup_data(args):
    """Create backup of workspace data."""
    try:
        # Initialize workspace and migration manager
        workspace = Workspace()
        migration_manager = create_migration_manager(workspace)
        
        # Get workspace to backup
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
            
        # Analyze workspace first
        legacy_data = migration_manager.detector.analyze_legacy_workspace(workspace_path)
        
        # Create backup
        backup_path = migration_manager.migrator._create_backup(workspace_path)
        print(f"✅ Backup created: {backup_path}")
        print(f"   - Pipelines: {legacy_data.pipeline_count}")
        print(f"   - Articles: {legacy_data.article_count}")
        print(f"   - Has LMDB data: {legacy_data.has_lmdb}")
        return 0
        
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return 1


def update_workspace_structure(args):
    """Update workspace directory structure to DDD format."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get workspace path
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
        
        # Create structure updater
        updater = WorkspaceStructureUpdater(workspace)
        
        # Run structure update
        if args.dry_run:
            print(f"DRY RUN: Would update workspace structure for {workspace_name}")
            # Show what would be done
            from writeit.migration.workspace_structure_updater import LegacyWorkspaceAnalyzer
            analyzer = LegacyWorkspaceAnalyzer()
            analysis = analyzer.analyze_workspace_structure(workspace_path)
            print(f"   - Has legacy structure: {analysis['has_legacy_structure']}")
            print(f"   - Missing directories: {analysis['missing_directories']}")
            print(f"   - Files to move: {len(analysis['files_to_move'])}")
            return 0
        
        success = updater.update_workspace_structure(workspace_name)
        
        if success:
            print(f"✅ Successfully updated workspace structure: {workspace_name}")
            
            # Validate structure if requested
            if args.validate:
                issues = updater.validate_updated_structure(workspace_path)
                if issues:
                    print(f"⚠️  Structure validation found {len(issues)} issues:")
                    for issue in issues:
                        print(f"     - {issue}")
                else:
                    print(f"✅ Structure validation passed")
            
            return 0
        else:
            print(f"❌ Workspace structure update failed: {workspace_name}")
            return 1
            
    except Exception as e:
        print(f"❌ Workspace structure update error: {e}")
        return 1


def update_cache_format(args):
    """Update cache format to new DDD-compatible format."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get workspace path
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
        
        # Create cache migration manager and updater
        cache_manager = create_cache_migration_manager()
        cache_updater = create_cache_format_updater(cache_manager)
        
        # Run cache format update
        if args.dry_run:
            print(f"DRY RUN: Would update cache format for {workspace_name}")
            # Analyze cache to show what would be done
            analyses = cache_manager.analyze_cache_migration_needs(workspace_path)
            if analyses:
                for analysis in analyses:
                    print(f"   - Cache format: {analysis.cache_format}")
                    print(f"   - Total entries: {analysis.total_entries}")
                    print(f"   - Has pickle data: {analysis.has_pickle_data}")
                    print(f"   - Expired entries: {analysis.expired_entries}")
            else:
                print("   - No cache found to migrate")
            return 0
        
        result = cache_updater.update_cache_format(
            workspace_path=workspace_path,
            backup=True,
            skip_pickle=not args.include_pickle,
            cleanup_expired=not args.keep_expired,
            dry_run=False
        )
        
        if result.success:
            print(f"✅ Successfully updated cache format: {workspace_name}")
            print(f"   - Updated entries: {result.updated_entries}")
            print(f"   - Skipped entries: {result.skipped_entries}")
            print(f"   - Cleaned entries: {result.cleaned_entries}")
            
            if result.warnings:
                print(f"   - {len(result.warnings)} warnings:")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    print(f"     - {warning}")
                if len(result.warnings) > 3:
                    print(f"     - ... and {len(result.warnings) - 3} more")
            
            # Validate cache format if requested
            if args.validate:
                issues = cache_updater.validate_cache_format(workspace_path)
                if issues:
                    print(f"⚠️  Cache validation found {len(issues)} issues:")
                    for issue in issues:
                        print(f"     - {issue}")
                else:
                    print(f"✅ Cache format validation passed")
            
            return 0
        else:
            print(f"❌ Cache format update failed: {workspace_name}")
            print(f"   - {result.message}")
            if result.errors:
                for error in result.errors:
                    print(f"     - {error}")
            return 1
            
    except Exception as e:
        print(f"❌ Cache format update error: {e}")
        return 1


def comprehensive_validation(args):
    """Perform comprehensive migration validation."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get workspace path
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
        
        # Create migration validator
        validator = create_migration_validator()
        
        # Run comprehensive validation
        result = validator.validate_complete_migration(workspace_path, workspace_name)
        
        # Display results
        status = "✅ PASSED" if result.success else "❌ FAILED"
        print(f"Migration Validation: {status}")
        print(f"Workspace: {result.workspace_name}")
        print(f"Migration Score: {result.migration_score:.1f}%")
        print(f"Message: {result.message}")
        
        # Show validation check results
        print(f"\nValidation Checks:")
        for check_name, passed in result.validation_checks.items():
            status_icon = "✅" if passed else "❌"
            check_display = check_name.replace('_', ' ').title()
            print(f"  {status_icon} {check_display}")
        
        # Show warnings
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings[:5]:  # Show first 5 warnings
                print(f"  ⚠️  {warning}")
            if len(result.warnings) > 5:
                print(f"  ... and {len(result.warnings) - 5} more warnings")
        
        # Show errors
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  💥 {error}")
        
        # Show recommendations
        if result.recommendations:
            print(f"\nRecommendations:")
            for recommendation in result.recommendations:
                print(f"  🔧 {recommendation}")
        
        # Generate detailed report if requested
        if args.report or args.output_file:
            report = validator.generate_validation_report(result)
            
            if args.output_file:
                output_path = Path(args.output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(report)
                print(f"\n📄 Detailed report saved to: {output_path}")
            else:
                # Print report to console
                print(f"\n" + "="*60)
                print("DETAILED VALIDATION REPORT")
                print("="*60)
                print(report)
        
        return 0 if result.success else 1
            
    except Exception as e:
        print(f"❌ Comprehensive validation error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="WriteIt Data Migration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate a specific workspace
  writeit migrate workspace default
  
  # Dry run migration
  writeit migrate workspace default --dry-run
  
  # Migrate all workspaces
  writeit migrate all
  
  # Validate migration
  writeit migrate validate default
  
  # Create backup
  writeit migrate backup default
  
  # Update workspace structure
  writeit migrate structure default
  
  # Update workspace structure with validation
  writeit migrate structure default --validate
  
  # Update cache format
  writeit migrate cache default
  
  # Update cache format with validation
  writeit migrate cache default --validate
  
  # Include pickle data in cache migration (not recommended)
  writeit migrate cache default --include-pickle
  
  # Comprehensive migration validation
  writeit migrate validate-all default
  
  # Generate detailed validation report
  writeit migrate validate-all default --report --output-file migration_report.md
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Workspace migration command
    workspace_parser = subparsers.add_parser(
        'workspace',
        help='Migrate a specific workspace'
    )
    workspace_parser.add_argument(
        'workspace_name',
        help='Name of workspace to migrate'
    )
    workspace_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    workspace_parser.add_argument(
        '--report',
        action='store_true',
        help='Generate migration report'
    )
    workspace_parser.set_defaults(func=migrate_workspace)
    
    # Migrate all workspaces command
    all_parser = subparsers.add_parser(
        'all',
        help='Migrate all available legacy workspaces'
    )
    all_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    all_parser.add_argument(
        '--batch',
        action='store_true',
        help='Run in batch mode without interactive prompts'
    )
    all_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed migration results'
    )
    all_parser.set_defaults(func=migrate_all_workspaces)
    
    # Validate migration command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate migrated workspace'
    )
    validate_parser.add_argument(
        'workspace_name',
        help='Name of workspace to validate'
    )
    validate_parser.set_defaults(func=validate_migration)
    
    # Backup command
    backup_parser = subparsers.add_parser(
        'backup',
        help='Create backup of workspace data'
    )
    backup_parser.add_argument(
        'workspace_name',
        help='Name of workspace to backup'
    )
    backup_parser.set_defaults(func=backup_data)
    
    # Workspace structure update command
    structure_parser = subparsers.add_parser(
        'structure',
        help='Update workspace directory structure to DDD format'
    )
    structure_parser.add_argument(
        'workspace_name',
        help='Name of workspace to update structure'
    )
    structure_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    structure_parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate structure after update'
    )
    structure_parser.set_defaults(func=update_workspace_structure)
    
    # Cache format update command
    cache_parser = subparsers.add_parser(
        'cache',
        help='Update cache format to new DDD-compatible format'
    )
    cache_parser.add_argument(
        'workspace_name',
        help='Name of workspace to update cache format'
    )
    cache_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    cache_parser.add_argument(
        '--include-pickle',
        action='store_true',
        help='Include pickle data in migration (not recommended for security)'
    )
    cache_parser.add_argument(
        '--keep-expired',
        action='store_true',
        help='Keep expired cache entries'
    )
    cache_parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate cache format after update'
    )
    cache_parser.set_defaults(func=update_cache_format)
    
    # Comprehensive validation command
    validate_parser = subparsers.add_parser(
        'validate-all',
        help='Comprehensive migration validation with detailed reporting'
    )
    validate_parser.add_argument(
        'workspace_name',
        help='Name of workspace to validate'
    )
    validate_parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed validation report'
    )
    validate_parser.add_argument(
        '--output-file',
        type=str,
        help='Save validation report to file'
    )
    validate_parser.set_defaults(func=comprehensive_validation)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())