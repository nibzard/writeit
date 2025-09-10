# ABOUTME: Template and style manager for workspace-aware resolution
# ABOUTME: Centralized logic for finding templates/styles across workspace and global scopes

from pathlib import Path
from typing import List, Optional, Tuple
from enum import Enum

from .workspace import Workspace


class TemplateScope(str, Enum):
    """Template/style scope enumeration."""
    WORKSPACE = "workspace"
    GLOBAL = "global"
    AUTO = "auto"  # Workspace first, then global


class TemplateType(str, Enum):
    """Template type enumeration."""
    PIPELINE = "pipeline"
    STYLE = "style"


class TemplateLocation:
    """Represents a located template/style with metadata."""
    
    def __init__(self, path: Path, scope: TemplateScope, workspace_name: Optional[str] = None):
        self.path = path
        self.scope = scope
        self.workspace_name = workspace_name
        self.name = path.stem
        self.exists = path.exists()
    
    def __str__(self) -> str:
        if self.scope == TemplateScope.GLOBAL:
            return f"{self.name} [Global]"
        else:
            return f"{self.name} [Workspace: {self.workspace_name}]"


class TemplateManager:
    """Manages template and style resolution across workspace and global scopes."""
    
    def __init__(self, workspace_manager: Optional[Workspace] = None):
        """Initialize template manager.
        
        Args:
            workspace_manager: Workspace manager instance (creates new if None)
        """
        self.workspace_manager = workspace_manager or Workspace()
    
    def resolve_template(
        self, 
        name: str, 
        template_type: TemplateType,
        workspace_name: Optional[str] = None,
        scope: TemplateScope = TemplateScope.AUTO
    ) -> Optional[TemplateLocation]:
        """Resolve a template/style location.
        
        Args:
            name: Template/style name (with or without .yaml extension)
            template_type: Type of template to resolve
            workspace_name: Workspace name (defaults to active workspace)
            scope: Resolution scope (auto, workspace, global)
            
        Returns:
            TemplateLocation if found, None otherwise
        """
        # Normalize name to include .yaml extension
        filename = name if name.endswith(('.yaml', '.yml')) else f"{name}.yaml"
        
        # Determine workspace to use
        if workspace_name is None:
            try:
                workspace_name = self.workspace_manager.get_active_workspace()
            except Exception:
                workspace_name = "default"
        
        # Build search locations based on scope
        locations = self._get_search_locations(filename, template_type, workspace_name, scope)
        
        # Return first existing location
        for location in locations:
            if location.exists:
                return location
        
        return None
    
    def list_templates(
        self, 
        template_type: TemplateType,
        workspace_name: Optional[str] = None,
        scope: TemplateScope = TemplateScope.AUTO
    ) -> List[TemplateLocation]:
        """List available templates/styles.
        
        Args:
            template_type: Type of templates to list
            workspace_name: Workspace name (defaults to active workspace)
            scope: Scope to search (auto, workspace, global)
            
        Returns:
            List of TemplateLocation objects
        """
        # Determine workspace to use
        if workspace_name is None:
            try:
                workspace_name = self.workspace_manager.get_active_workspace()
            except Exception:
                workspace_name = "default"
        
        templates = []
        seen_names = set()
        
        # Get search directories based on scope
        directories = self._get_search_directories(template_type, workspace_name, scope)
        
        for directory, dir_scope, dir_workspace in directories:
            if not directory.exists():
                continue
                
            for template_file in directory.glob("*.yaml"):
                name = template_file.stem
                
                # Skip duplicates (workspace takes precedence over global)
                if scope == TemplateScope.AUTO and name in seen_names:
                    continue
                
                location = TemplateLocation(template_file, dir_scope, dir_workspace)
                templates.append(location)
                seen_names.add(name)
        
        return sorted(templates, key=lambda t: (t.scope.value, t.name))
    
    def create_template(
        self, 
        name: str, 
        template_type: TemplateType,
        content: str,
        workspace_name: Optional[str] = None,
        scope: TemplateScope = TemplateScope.WORKSPACE
    ) -> TemplateLocation:
        """Create a new template/style.
        
        Args:
            name: Template/style name
            template_type: Type of template to create
            content: Template content
            workspace_name: Workspace name (required for workspace scope)
            scope: Where to create the template (workspace or global)
            
        Returns:
            TemplateLocation of created template
            
        Raises:
            ValueError: If template already exists or invalid parameters
        """
        # Normalize name
        filename = name if name.endswith(('.yaml', '.yml')) else f"{name}.yaml"
        
        # Determine target directory
        if scope == TemplateScope.GLOBAL:
            target_dir = self._get_global_directory(template_type)
            location_workspace = None
        elif scope == TemplateScope.WORKSPACE:
            if workspace_name is None:
                workspace_name = self.workspace_manager.get_active_workspace()
            target_dir = self._get_workspace_directory(template_type, workspace_name)
            location_workspace = workspace_name
        else:
            raise ValueError(f"Cannot create template with scope '{scope}'. Use 'workspace' or 'global'.")
        
        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if template already exists
        target_path = target_dir / filename
        if target_path.exists():
            raise ValueError(f"Template '{name}' already exists in {scope} scope")
        
        # Write template content
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return TemplateLocation(target_path, scope, location_workspace)
    
    def copy_template(
        self,
        source_name: str,
        dest_name: str,
        template_type: TemplateType,
        source_workspace: Optional[str] = None,
        dest_workspace: Optional[str] = None,
        dest_scope: TemplateScope = TemplateScope.WORKSPACE
    ) -> TemplateLocation:
        """Copy a template from one location to another.
        
        Args:
            source_name: Source template name
            dest_name: Destination template name
            template_type: Type of template
            source_workspace: Source workspace (None for global or auto-resolve)
            dest_workspace: Destination workspace (required for workspace scope)
            dest_scope: Destination scope
            
        Returns:
            TemplateLocation of copied template
            
        Raises:
            ValueError: If source not found or destination exists
        """
        # Find source template
        source_location = self.resolve_template(
            source_name, 
            template_type, 
            source_workspace,
            TemplateScope.AUTO
        )
        
        if source_location is None:
            raise ValueError(f"Source template '{source_name}' not found")
        
        # Read source content
        with open(source_location.path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create destination template
        return self.create_template(
            dest_name,
            template_type,
            content,
            dest_workspace,
            dest_scope
        )
    
    def _get_search_locations(
        self, 
        filename: str, 
        template_type: TemplateType,
        workspace_name: str,
        scope: TemplateScope
    ) -> List[TemplateLocation]:
        """Get ordered list of search locations."""
        locations = []
        
        if scope in (TemplateScope.AUTO, TemplateScope.WORKSPACE):
            # Add workspace locations
            workspace_dir = self._get_workspace_directory(template_type, workspace_name)
            locations.append(TemplateLocation(
                workspace_dir / filename, 
                TemplateScope.WORKSPACE, 
                workspace_name
            ))
        
        if scope in (TemplateScope.AUTO, TemplateScope.GLOBAL):
            # Add global location
            global_dir = self._get_global_directory(template_type)
            locations.append(TemplateLocation(
                global_dir / filename,
                TemplateScope.GLOBAL
            ))
        
        return locations
    
    def _get_search_directories(
        self, 
        template_type: TemplateType,
        workspace_name: str,
        scope: TemplateScope
    ) -> List[Tuple[Path, TemplateScope, Optional[str]]]:
        """Get directories to search for templates."""
        directories = []
        
        if scope in (TemplateScope.AUTO, TemplateScope.WORKSPACE):
            workspace_dir = self._get_workspace_directory(template_type, workspace_name)
            directories.append((workspace_dir, TemplateScope.WORKSPACE, workspace_name))
        
        if scope in (TemplateScope.AUTO, TemplateScope.GLOBAL):
            global_dir = self._get_global_directory(template_type)
            directories.append((global_dir, TemplateScope.GLOBAL, None))
        
        return directories
    
    def _get_workspace_directory(self, template_type: TemplateType, workspace_name: str) -> Path:
        """Get workspace directory for template type."""
        if template_type == TemplateType.PIPELINE:
            return self.workspace_manager.get_workspace_templates_dir(workspace_name)
        else:  # TemplateType.STYLE
            return self.workspace_manager.get_workspace_styles_dir(workspace_name)
    
    def _get_global_directory(self, template_type: TemplateType) -> Path:
        """Get global directory for template type."""
        if template_type == TemplateType.PIPELINE:
            return self.workspace_manager.templates_dir
        else:  # TemplateType.STYLE
            return self.workspace_manager.styles_dir