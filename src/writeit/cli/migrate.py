"""Command-line interface for WriteIt data migration.

This module provides CLI commands for migrating existing WriteIt data
from legacy formats to the new DDD-based structure.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.migration.data_migration import DataMigrator, create_migration_report


def migrate_workspace(args):
    """Migrate a single workspace."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get workspace path
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
            
        # Create migrator
        migrator = DataMigrator(workspace)
        
        # Run migration
        if args.dry_run:
            print(f"DRY RUN: Would migrate workspace {workspace_name}")
            return 0
            
        success = migrator.run_full_migration(workspace_path)
        
        if success:
            print(f"✅ Successfully migrated workspace: {workspace_name}")
            
            # Generate report
            if args.report:
                report = create_migration_report(migrator)
                report_path = Path(f"migration_report_{workspace_name}.md")
                with open(report_path, 'w') as f:
                    f.write(report)
                print(f"📄 Migration report saved to: {report_path}")
                
            return 0
        else:
            print(f"❌ Migration failed for workspace: {workspace_name}")
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1


def migrate_all_workspaces(args):
    """Migrate all available workspaces."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get all workspaces
        workspaces = workspace.list_workspaces()
        
        if not workspaces:
            print("No workspaces found")
            return 0
            
        print(f"Found {len(workspaces)} workspaces to migrate")
        
        # Migrate each workspace
        success_count = 0
        for workspace_name in workspaces:
            print(f"\nMigrating workspace: {workspace_name}")
            
            workspace_path = workspace.get_workspace_path(workspace_name)
            migrator = DataMigrator(workspace)
            
            if args.dry_run:
                print(f"DRY RUN: Would migrate workspace {workspace_name}")
                success_count += 1
                continue
                
            success = migrator.run_full_migration(workspace_path)
            if success:
                print(f"✅ Successfully migrated: {workspace_name}")
                success_count += 1
            else:
                print(f"❌ Migration failed: {workspace_name}")
                
        print(f"\n📊 Migration Summary:")
        print(f"   Total workspaces: {len(workspaces)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(workspaces) - success_count}")
        
        if success_count == len(workspaces):
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1


def validate_migration(args):
    """Validate migrated workspaces."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get workspace to validate
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
            
        # Create migrator for validation
        migrator = DataMigrator(workspace)
        
        # Validate
        issues = migrator.validate_migration(workspace_path)
        
        if issues:
            print(f"❌ Migration validation failed for {workspace_name}:")
            for issue in issues:
                print(f"   - {issue}")
            return 1
        else:
            print(f"✅ Migration validation passed for {workspace_name}")
            return 0
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return 1


def backup_data(args):
    """Create backup of workspace data."""
    try:
        # Initialize workspace
        workspace = Workspace()
        
        # Get workspace to backup
        workspace_name = args.workspace_name
        workspace_path = workspace.get_workspace_path(workspace_name)
        
        if not workspace_path.exists():
            print(f"Workspace not found: {workspace_path}")
            return 1
            
        # Create migrator
        migrator = DataMigrator(workspace)
        
        # Create backup
        backup_path = migrator.backup_legacy_data(workspace_path)
        print(f"✅ Backup created: {backup_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Backup error: {e}")
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
        help='Migrate all available workspaces'
    )
    all_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
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
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())