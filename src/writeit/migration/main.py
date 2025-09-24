"""Main entry point for WriteIt DDD Migration.

This script provides the main entry point for the integrated WriteIt DDD migration
system. It can be run as a standalone script or imported as a module.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.migration.integrated_migration import IntegratedMigration


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="WriteIt DDD Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete migration for all workspaces
  python main.py
  
  # Run migration for specific workspace
  python main.py --workspace default
  
  # Dry run migration
  python main.py --dry-run
  
  # Skip backup creation
  python main.py --no-backup
  
  # Rollback migration
  python main.py --rollback
  
  # Show migration status
  python main.py --status
        """
    )
    
    # Migration options
    parser.add_argument(
        '--workspace', '-w',
        help='Name of specific workspace to migrate (default: all workspaces)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation (not recommended)'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback migration using backup'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show migration status and statistics'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
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
        # Initialize workspace and migration system
        workspace = Workspace()
        migration = IntegratedMigration(workspace)
        
        # Handle rollback
        if args.rollback:
            print("🔄 Rolling back migration...")
            success = migration.rollback_migration(args.workspace)
            if success:
                print("✅ Rollback completed successfully")
                return 0
            else:
                print("❌ Rollback failed")
                return 1
                
        # Handle status display
        if args.status:
            print("📊 Migration Status:")
            state = migration.get_migration_state()
            
            if state["completed_at"]:
                print(f"   Status: {'✅ Completed' if state['success'] else '❌ Failed'}")
                print(f"   Started: {state['started_at']}")
                print(f"   Completed: {state['completed_at']}")
                print(f"   Phases: {len(state['phases_completed'])}")
                print(f"   Errors: {len(state['errors'])}")
                print(f"   Warnings: {len(state['warnings'])}")
            else:
                print("   Status: Not started")
                
            return 0
            
        # Handle dry run
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print("This would perform the following migration:")
            print("  1. Pre-migration checks and backup")
            print("  2. Legacy data format conversion")
            print("  3. Workspace structure updates")
            print("  4. Configuration migration")
            print("  5. Cache format updates")
            print("  6. Post-migration validation")
            print("  7. Final cleanup and reporting")
            return 0
            
        # Run migration
        workspace_name = args.workspace
        backup = not args.no_backup
        
        print("🚀 Starting WriteIt DDD Migration...")
        if workspace_name:
            print(f"Target workspace: {workspace_name}")
        else:
            print("Target: All workspaces")
            
        if not backup:
            print("⚠️  WARNING: Skipping backup creation")
            
        success = migration.start_migration(workspace_name, backup)
        
        if success:
            print("\n🎉 Migration completed successfully!")
            return 0
        else:
            print("\n❌ Migration failed!")
            
            # Show errors if any
            state = migration.get_migration_state()
            if state["errors"]:
                print("\nErrors encountered:")
                for error in state["errors"]:
                    print(f"  - {error}")
                    
            return 1
        
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
    if not args.status and not args.dry_run:  # Skip validation for status and dry run
        if not validate_environment():
            return 1
    
    # Run migration
    return run_migration(args)


if __name__ == "__main__":
    sys.exit(main())