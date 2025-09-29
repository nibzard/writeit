"""Output Export Service.

Handles saving pipeline outputs to workspace directories with proper organization
and metadata. Provides markdown export with comprehensive metadata headers.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import yaml

from ....errors import WriteItError


class OutputExportError(WriteItError):
    """Raised when output export operations fail."""
    pass


@dataclass
class ExportMetadata:
    """Metadata for exported content."""
    
    pipeline_name: str
    workspace_name: str
    execution_id: str
    created_at: datetime
    template_version: Optional[str] = None
    model_used: Optional[str] = None
    total_steps: int = 0
    token_usage: Dict[str, int] = None
    execution_time_seconds: Optional[float] = None
    
    def __post_init__(self):
        if self.token_usage is None:
            self.token_usage = {"input": 0, "output": 0, "total": 0}


@dataclass
class ExportResult:
    """Result of an export operation."""
    
    success: bool
    file_path: Optional[Path] = None
    error_message: Optional[str] = None
    metadata: Optional[ExportMetadata] = None
    
    @classmethod
    def success_result(cls, file_path: Path, metadata: ExportMetadata) -> 'ExportResult':
        """Create a successful export result."""
        return cls(success=True, file_path=file_path, metadata=metadata)
    
    @classmethod
    def error_result(cls, error_message: str) -> 'ExportResult':
        """Create a failed export result."""
        return cls(success=False, error_message=error_message)


class OutputExportService:
    """
    Service for exporting pipeline outputs to workspace directories.
    
    Handles:
    - Creating output directories
    - Generating markdown files with metadata
    - File naming and organization
    - Workspace isolation
    """
    
    def __init__(self, workspace_root: Path):
        """Initialize the export service.
        
        Args:
            workspace_root: Root directory for workspaces (e.g., ~/.writeit)
        """
        self.workspace_root = workspace_root
    
    async def export_pipeline_output(
        self,
        content: str,
        metadata: ExportMetadata,
        filename_override: Optional[str] = None
    ) -> ExportResult:
        """
        Export pipeline output as a markdown file.
        
        Args:
            content: The content to export
            metadata: Export metadata
            filename_override: Optional custom filename (without extension)
            
        Returns:
            Export result with file path or error information
        """
        try:
            # Create output directory
            output_dir = self._get_output_directory(metadata.workspace_name)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = self._generate_filename(metadata, filename_override)
            file_path = output_dir / f"{filename}.md"
            
            # Generate markdown content with metadata header
            markdown_content = self._create_markdown_with_metadata(content, metadata)
            
            # Write to file
            file_path.write_text(markdown_content, encoding='utf-8')
            
            return ExportResult.success_result(file_path, metadata)
            
        except Exception as e:
            return ExportResult.error_result(f"Failed to export output: {str(e)}")
    
    async def export_step_outputs(
        self,
        step_results: Dict[str, str],
        metadata: ExportMetadata,
        include_intermediate: bool = False
    ) -> ExportResult:
        """
        Export all step outputs, optionally including intermediate results.
        
        Args:
            step_results: Dictionary of step_name -> output
            metadata: Export metadata
            include_intermediate: Whether to include intermediate steps
            
        Returns:
            Export result for the combined output file
        """
        try:
            # Get the final output (last step or specific final step)
            final_output = self._extract_final_output(step_results)
            
            if include_intermediate:
                # Create a comprehensive document with all steps
                combined_content = self._create_comprehensive_document(step_results, metadata)
            else:
                combined_content = final_output
            
            # Export the content
            return await self.export_pipeline_output(combined_content, metadata)
            
        except Exception as e:
            return ExportResult.error_result(f"Failed to export step outputs: {str(e)}")
    
    def _get_output_directory(self, workspace_name: str) -> Path:
        """Get the output directory for a workspace."""
        return self.workspace_root / "workspaces" / workspace_name / "outputs"
    
    def _generate_filename(self, metadata: ExportMetadata, override: Optional[str] = None) -> str:
        """Generate a filename for the export."""
        if override:
            return override
        
        # Create timestamp
        timestamp = metadata.created_at.strftime("%Y%m%d_%H%M%S")
        
        # Clean pipeline name
        clean_name = metadata.pipeline_name.replace(" ", "_").lower()
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in "_-")
        
        return f"{clean_name}_{timestamp}"
    
    def _create_markdown_with_metadata(self, content: str, metadata: ExportMetadata) -> str:
        """Create markdown content with YAML front matter metadata."""
        # Create YAML front matter
        frontmatter = {
            "title": f"Generated by {metadata.pipeline_name}",
            "pipeline": metadata.pipeline_name,
            "workspace": metadata.workspace_name,
            "execution_id": metadata.execution_id,
            "created_at": metadata.created_at.isoformat(),
            "generator": "WriteIt CLI",
            "total_steps": metadata.total_steps,
        }
        
        # Add optional metadata
        if metadata.template_version:
            frontmatter["template_version"] = metadata.template_version
        if metadata.model_used:
            frontmatter["model_used"] = metadata.model_used
        if metadata.execution_time_seconds:
            frontmatter["execution_time_seconds"] = metadata.execution_time_seconds
        if metadata.token_usage:
            frontmatter["token_usage"] = metadata.token_usage
        
        # Generate YAML front matter
        yaml_header = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        
        # Combine with content
        return f"---\n{yaml_header}---\n\n{content.strip()}\n"
    
    def _extract_final_output(self, step_results: Dict[str, str]) -> str:
        """Extract the final output from step results."""
        if not step_results:
            return ""
        
        # Priority order for final output
        final_step_names = ["polish", "finalize", "complete", "finish", "export"]
        
        # Try to find a final step
        for step_name in final_step_names:
            if step_name in step_results and step_results[step_name].strip():
                return step_results[step_name].strip()
        
        # Fall back to the last step with content
        for step_name in reversed(list(step_results.keys())):
            if step_results[step_name].strip():
                return step_results[step_name].strip()
        
        # If all else fails, concatenate all results
        return "\n\n".join(result.strip() for result in step_results.values() if result.strip())
    
    def _create_comprehensive_document(self, step_results: Dict[str, str], metadata: ExportMetadata) -> str:
        """Create a comprehensive document including all intermediate steps."""
        parts = []
        
        # Add main content (final output)
        final_output = self._extract_final_output(step_results)
        if final_output:
            parts.append(final_output)
        
        # Add appendix with intermediate steps
        if len(step_results) > 1:
            parts.append("\n---\n## Pipeline Steps\n")
            parts.append("*The following shows the intermediate steps used to generate this content:*\n")
            
            for i, (step_name, result) in enumerate(step_results.items(), 1):
                if result.strip():
                    parts.append(f"\n### Step {i}: {step_name.title()}\n")
                    parts.append(result.strip())
        
        return "\n\n".join(parts)
    
    async def get_recent_exports(
        self,
        workspace_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recently exported files from a workspace.
        
        Args:
            workspace_name: Name of the workspace
            limit: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            output_dir = self._get_output_directory(workspace_name)
            
            if not output_dir.exists():
                return []
            
            # Get all markdown files, sorted by modification time
            md_files = sorted(
                output_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:limit]
            
            # Extract file information
            file_info = []
            for file_path in md_files:
                try:
                    # Try to extract metadata from front matter
                    content = file_path.read_text(encoding='utf-8')
                    metadata = self._extract_metadata_from_file(content)
                    
                    file_info.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "created_at": datetime.fromtimestamp(file_path.stat().st_ctime),
                        "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime),
                        "metadata": metadata
                    })
                except Exception:
                    # Skip files that can't be processed
                    continue
            
            return file_info
            
        except Exception as e:
            raise OutputExportError(f"Failed to get recent exports: {str(e)}")
    
    def _extract_metadata_from_file(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract YAML front matter from a markdown file."""
        try:
            if not content.startswith("---\n"):
                return None
            
            end_marker = content.find("\n---\n", 4)
            if end_marker == -1:
                return None
            
            yaml_content = content[4:end_marker]
            return yaml.safe_load(yaml_content)
        except Exception:
            return None