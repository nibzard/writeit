# ABOUTME: Migration utilities for converting local workspaces to centralized ~/.writeit
# ABOUTME: Handles detection and migration of existing local .writeit directories
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml
import datetime

class WorkspaceMigrator:
    """Handles migration from local workspaces to centralized ~/.writeit structure."""
    
    def __init__(self, workspace_manager):
        """Initialize migrator.
        
        Args:
            workspace_manager: Workspace instance for accessing centralized structure
        """
        self.workspace_manager = workspace_manager
    
    def detect_local_workspaces(self, search_paths: Optional[List[Path]] = None) -> List[Path]:
        """Detect existing local .writeit directories.
        
        Args:
            search_paths: Paths to search (defaults to common locations)
            
        Returns:
            List of paths containing .writeit directories
        """
        if search_paths is None:
            search_paths = [
                Path.home(),  # User home directory
                Path.cwd(),   # Current working directory
                Path.home() / "Documents",
                Path.home() / "Projects",
                Path.home() / "Development",
                Path.home() / "dev",
            ]
        
        found_workspaces = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # Look for .writeit directories
            try:
                for item in search_path.rglob(".writeit"):
                    if item.is_dir():
                        found_workspaces.append(item.parent)
            except PermissionError:
                # Skip directories we can't access
                continue
        
        return list(set(found_workspaces))  # Remove duplicates
    
    def analyze_local_workspace(self, workspace_path: Path) -> Dict[str, any]:
        """Analyze a local workspace to understand its structure.
        
        Args:
            workspace_path: Path containing .writeit directory
            
        Returns:
            Analysis results with migration recommendations
        """
        writeit_dir = workspace_path / ".writeit"
        if not writeit_dir.exists():
            raise ValueError(f"No .writeit directory found in {workspace_path}")
        
        analysis = {
            "path": workspace_path,
            "writeit_dir": writeit_dir,
            "has_config": False,
            "has_pipelines": False,
            "has_articles": False,
            "has_lmdb": False,
            "config_data": None,
            "pipeline_count": 0,
            "article_count": 0,
            "recommended_workspace_name": None,
            "migration_complexity": "simple"
        }
        
        # Check for config files
        config_file = writeit_dir / "config.yaml"
        if config_file.exists():
            analysis["has_config"] = True
            try:
                with open(config_file, 'r') as f:
                    analysis["config_data"] = yaml.safe_load(f)
            except yaml.YAMLError:
                pass
        
        # Check for pipelines
        pipelines_dir = writeit_dir / "pipelines"
        if pipelines_dir.exists():
            analysis["has_pipelines"] = True
            pipeline_files = list(pipelines_dir.glob("*.yaml")) + list(pipelines_dir.glob("*.yml"))
            analysis["pipeline_count"] = len(pipeline_files)
        
        # Check for articles
        articles_dir = writeit_dir / "articles"
        if articles_dir.exists():
            analysis["has_articles"] = True
            article_files = list(articles_dir.glob("*.md")) + list(articles_dir.glob("*.txt"))
            analysis["article_count"] = len(article_files)
        
        # Check for LMDB data
        lmdb_files = list(writeit_dir.glob("*.mdb")) + list(writeit_dir.glob("*.lmdb"))
        if lmdb_files:
            analysis["has_lmdb"] = True
            analysis["migration_complexity"] = "moderate"
        
        # Suggest workspace name based on directory
        analysis["recommended_workspace_name"] = self._suggest_workspace_name(workspace_path)
        
        return analysis
    
    def migrate_local_workspace(self, workspace_path: Path, target_workspace_name: Optional[str] = None, overwrite: bool = False) -> Tuple[bool, str]:
        """Migrate a local workspace to centralized structure.
        
        Args:
            workspace_path: Path containing .writeit directory to migrate
            target_workspace_name: Name for new workspace (auto-generated if None)
            overwrite: Whether to overwrite existing workspace
            
        Returns:
            Tuple of (success, message)
        """
        try:
            analysis = self.analyze_local_workspace(workspace_path)
        except ValueError as e:
            return False, str(e)
        
        if target_workspace_name is None:
            target_workspace_name = analysis["recommended_workspace_name"]
        
        # Check if target workspace already exists
        if self.workspace_manager.workspace_exists(target_workspace_name):
            if not overwrite:
                return False, f"Workspace '{target_workspace_name}' already exists. Use overwrite=True to replace it."
            self.workspace_manager.remove_workspace(target_workspace_name)
        
        # Create new centralized workspace
        try:
            workspace_dir = self.workspace_manager.create_workspace(target_workspace_name)
        except ValueError as e:
            return False, f"Failed to create workspace: {e}"
        
        # Copy data from local workspace
        local_writeit = analysis["writeit_dir"]
        
        # Copy pipelines
        if analysis["has_pipelines"]:
            local_pipelines = local_writeit / "pipelines"
            target_pipelines = workspace_dir / "pipelines"
            self._copy_directory_contents(local_pipelines, target_pipelines)
        
        # Copy articles
        if analysis["has_articles"]:
            local_articles = local_writeit / "articles"
            target_articles = workspace_dir / "articles"
            self._copy_directory_contents(local_articles, target_articles)
        
        # Copy LMDB files
        if analysis["has_lmdb"]:
            for lmdb_file in local_writeit.glob("*.mdb"):
                shutil.copy2(lmdb_file, workspace_dir)
            for lmdb_file in local_writeit.glob("*.lmdb"):
                shutil.copy2(lmdb_file, workspace_dir)
        
        # Migrate configuration
        if analysis["has_config"] and analysis["config_data"]:
            self._migrate_config(analysis["config_data"], target_workspace_name)
        
        return True, f"Successfully migrated to workspace '{target_workspace_name}'"
    
    def create_migration_backup(self, workspace_path: Path) -> Path:
        """Create a backup of a local workspace before migration.
        
        Args:
            workspace_path: Path containing .writeit directory
            
        Returns:
            Path to backup directory
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"writeit_backup_{workspace_path.name}_{timestamp}"
        backup_dir = workspace_path.parent / backup_name
        
        local_writeit = workspace_path / ".writeit"
        shutil.copytree(local_writeit, backup_dir)
        
        return backup_dir
    
    def _suggest_workspace_name(self, workspace_path: Path) -> str:
        """Suggest a workspace name based on directory structure.
        
        Args:
            workspace_path: Path containing .writeit directory
            
        Returns:
            Suggested workspace name
        """
        # Use directory name, cleaned up for workspace naming
        name = workspace_path.name.lower()
        
        # Replace common characters with underscores
        name = name.replace(" ", "_").replace("-", "_")
        
        # Remove non-alphanumeric characters except underscores
        name = "".join(c for c in name if c.isalnum() or c == "_")
        
        # Ensure it starts with a letter or underscore
        if name and not (name[0].isalpha() or name[0] == "_"):
            name = f"workspace_{name}"
        
        # Fallback if empty
        if not name:
            name = "migrated_workspace"
        
        return name
    
    def _copy_directory_contents(self, source: Path, target: Path) -> None:
        """Copy contents of source directory to target directory.
        
        Args:
            source: Source directory
            target: Target directory
        """
        if not source.exists():
            return
        
        target.mkdir(parents=True, exist_ok=True)
        
        for item in source.iterdir():
            if item.is_file():
                shutil.copy2(item, target)
            elif item.is_dir():
                target_subdir = target / item.name
                shutil.copytree(item, target_subdir, dirs_exist_ok=True)
    
    def _migrate_config(self, config_data: Dict[str, any], workspace_name: str) -> None:
        """Migrate configuration data to new workspace.
        
        Args:
            config_data: Configuration data from local workspace
            workspace_name: Target workspace name
        """
        # For now, just log that we found config - more sophisticated migration
        # can be added as needed when we understand the actual config structure
        pass


def find_and_migrate_workspaces(workspace_manager, search_paths: Optional[List[Path]] = None, interactive: bool = True) -> List[Tuple[Path, bool, str]]:
    """Find and optionally migrate local workspaces.
    
    Args:
        workspace_manager: Workspace instance
        search_paths: Paths to search for local workspaces
        interactive: Whether to prompt for migration decisions
        
    Returns:
        List of (workspace_path, migrated, message) tuples
    """
    migrator = WorkspaceMigrator(workspace_manager)
    found_workspaces = migrator.detect_local_workspaces(search_paths)
    results = []
    
    if not found_workspaces:
        return results
    
    for workspace_path in found_workspaces:
        if interactive:
            print(f"\nFound local workspace: {workspace_path}")
            analysis = migrator.analyze_local_workspace(workspace_path)
            print(f"  - Pipelines: {analysis['pipeline_count']}")
            print(f"  - Articles: {analysis['article_count']}")
            print(f"  - Has LMDB data: {analysis['has_lmdb']}")
            print(f"  - Suggested name: {analysis['recommended_workspace_name']}")
            
            migrate = input("Migrate this workspace? (y/n): ").lower().startswith('y')
            if not migrate:
                results.append((workspace_path, False, "Skipped by user"))
                continue
        
        success, message = migrator.migrate_local_workspace(workspace_path)
        results.append((workspace_path, success, message))
    
    return results