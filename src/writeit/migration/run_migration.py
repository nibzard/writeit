"""Main migration script for WriteIt DDD refactoring.

This script provides a complete migration solution for converting legacy WriteIt data
to the new DDD-based structure. It can be run as a standalone script or imported
as a module.

Usage:
    # Run migration for specific workspace
    python -m writeit.migration.run_migration --workspace default
    
    # Run migration for all workspaces
    python -m writeit.migration.run_migration --all
    
    # Dry run to see what would be migrated
    python -m writeit.migration.run_migration --all --dry-run
    
    # Generate report only
    python -m writeit.migration.run_migration --report-only
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.migration.migration_runner import MigrationRunner


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="WriteIt DDD Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate specific workspace
  python run_migration.py --workspace default
  
  # Migrate all workspaces
  python run_migration.py --all
  
  # Dry run migration
  python run_migration.py --all --dry-run
  
  # Generate report only
  python run_migration.py --report-only
  
  # Rollback migration
  python run_migration.py --rollback default
        """
    )
    
    # Migration target options
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        '--workspace', '-w',
        help='Name of specific workspace to migrate'
    )
    target_group.add_argument(
        '--all', '-a',
        action='store_true',
        help='Migrate all available workspaces'
    )
    target_group.add_argument(
        '--report-only',
        action='store_true',
        help='Generate migration report only (no migration)'
    )
    target_group.add_argument(
        '--rollback', '-r',
        help='Rollback migration for specified workspace'
    )
    
    # Migration options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    parser.add_argument(
        '--output-report',
        type=Path,
        help='Path to save migration report (default: migration_report.md)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if validation fails'
    )
    
    return parser


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    import logging
    
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_environment() -> bool:
    """Validate that migration environment is ready.
    
    Returns:
        True if environment is valid, False otherwise
    """
    try:
        # Check if workspace can be initialized
        workspace = Workspace()
        
        # Check if ~/.writeit exists
        if not workspace.base_dir.exists():
            print("Error: ~/.writeit directory not found")
            print("Please run 'writeit init' first")
            return False
            
        return True
        
    except Exception as e:
        print(f"Environment validation failed: {e}")
        return False


def run_migration(args) -> int:
    """Run the migration process.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Initialize workspace and runner
        workspace = Workspace()
        runner = MigrationRunner(workspace)
        
        # Handle rollback
        if args.rollback:
            print(f"Rolling back migration for workspace: {args.rollback}")
            success = runner.rollback_migration(args.rollback)
            if success:
                print("✅ Rollback completed successfully")
                return 0
            else:
                print("❌ Rollback failed")
                return 1
                
        # Handle report generation only
        if args.report_only:
            print("Generating migration report...")
            report = runner.generate_migration_report(args.output_report)
            print("✅ Report generated successfully")
            if args.output_report:
                print(f"Report saved to: {args.output_report}")
            return 0
            
        # Handle dry run
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            
        # Determine migration target
        workspace_name = args.workspace if args.workspace else None
        migrate_all = args.all
        
        # Run migration
        if migrate_all:
            print("🚀 Starting migration for all workspaces...")
            results = runner.run_full_migration()
        else:
            print(f"🚀 Starting migration for workspace: {workspace_name}")
            results = runner.run_full_migration(workspace_name)
            
        # Display results
        print("\n" + "="*50)
        print("MIGRATION RESULTS")
        print("="*50)
        
        if results["success"]:
            print("✅ Migration completed successfully!")
            
            summary = results.get("summary", {})
            if summary:
                print(f"\n📊 Summary:")
                print(f"   Workspaces Attempted: {summary.get('workspaces_attempted', 0)}")
                print(f"   Workspaces Succeeded: {summary.get('workspaces_succeeded', 0)}")
                print(f"   Workspaces Failed: {summary.get('workspaces_failed', 0)}")
                
            # Display workspace details
            details = results.get("details", {})
            for ws_name, ws_result in details.items():
                print(f"\n📁 Workspace: {ws_name}")
                print(f"   Status: {'✅ Success' if ws_result.get('success') else '❌ Failed'}")
                print(f"   Files Processed: {ws_result.get('files_processed', 0)}")
                print(f"   Steps Completed: {', '.join(ws_result.get('steps_completed', []))}")
                
                # Display errors if any
                errors = ws_result.get("errors", [])
                if errors:
                    print("   Errors:")
                    for error in errors:
                        print(f"     - {error}")
                        
        else:
            print("❌ Migration failed!")
            
            # Display errors
            errors = results.get("errors", [])
            if errors:
                print("\n❌ Errors:")
                for error in errors:
                    print(f"   - {error}")
                    
        # Generate report
        if args.output_report or args.verbose:
            report_path = args.output_report or Path("migration_report.md")
            runner.generate_migration_report(report_path)
            print(f"\n📄 Migration report saved to: {report_path}")
            
        return 0 if results["success"] else 1
        
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Migration error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate environment
    if not validate_environment():
        return 1
        
    # Run migration
    return run_migration(args)


if __name__ == "__main__":
    sys.exit(main())