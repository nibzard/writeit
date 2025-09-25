"""Comprehensive data migration service for DDD transformation.

Migrates legacy data formats to new DDD-compliant structures including:
- Legacy token usage data to new TokenUsage entities
- Legacy cache entries to new cache structure
- Legacy workspace configurations to new domain entities
- Legacy pipeline data to new pipeline entities
"""

import asyncio
import json
import shutil
import sqlite3
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import yaml
import lmdb

from writeit.domains.execution.entities.token_usage import (
    TokenUsage, TokenMetrics, CostBreakdown, UsageType, UsageCategory
)
from writeit.domains.execution.entities.llm_provider import LLMProvider
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.pipeline.entities.pipeline_template import PipelineTemplate
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.content.entities.template import Template
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.style_name import StyleName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.storage.adapter import create_storage_adapter


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    
    success: bool
    message: str
    migrated_count: int = 0
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)
    backup_path: Optional[Path] = None
    duration_seconds: float = 0.0


@dataclass
class MigrationContext:
    """Context for migration operations."""
    
    source_path: Path
    target_path: Path
    workspace_name: str
    backup_path: Optional[Path] = None
    dry_run: bool = False
    verbose: bool = False


class DataMigrationService:
    """Comprehensive data migration service for DDD transformation."""
    
    def __init__(self, workspace_manager=None):
        """Initialize migration service.
        
        Args:
            workspace_manager: Workspace manager instance
        """
        self.workspace_manager = workspace_manager
        self.migration_log: List[Dict[str, Any]] = []
        
    async def migrate_all_data(
        self, 
        source_workspace_path: Path,
        workspace_name: str,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> MigrationResult:
        """Perform comprehensive data migration.
        
        Args:
            source_workspace_path: Path to legacy workspace
            workspace_name: Name for new workspace
            dry_run: If True, only analyze without making changes
            create_backup: Whether to create backup before migration
            
        Returns:
            MigrationResult with details
        """
        start_time = datetime.now()
        
        # Validate source workspace exists
        if not source_workspace_path.exists():
            return MigrationResult(
                success=False,
                message=f"Source workspace does not exist: {source_workspace_path}",
                error_count=1
            )
        
        # Create backup if requested
        backup_path = None
        if create_backup and not dry_run:
            backup_path = await self._create_backup(source_workspace_path, workspace_name)
        
        # Initialize migration context
        context = MigrationContext(
            source_path=source_workspace_path,
            target_path=Path.home() / ".writeit" / "workspaces" / workspace_name,
            workspace_name=workspace_name,
            backup_path=backup_path,
            dry_run=dry_run
        )
        
        # Perform migration phases
        results = []
        
        try:
            # Phase 1: Workspace structure migration
            workspace_result = await self._migrate_workspace_structure(context)
            results.append(workspace_result)
            
            # Phase 2: Configuration migration
            config_result = await self._migrate_configuration(context)
            results.append(config_result)
            
            # Phase 3: Token usage migration
            token_result = await self._migrate_token_usage(context)
            results.append(token_result)
            
            # Phase 4: Cache migration
            cache_result = await self._migrate_cache(context)
            results.append(cache_result)
            
            # Phase 5: Pipeline and template migration
            pipeline_result = await self._migrate_pipelines_and_templates(context)
            results.append(pipeline_result)
            
            # Calculate overall result
            total_migrated = sum(r.migrated_count for r in results)
            total_errors = sum(r.error_count for r in results)
            all_warnings = []
            for r in results:
                all_warnings.extend(r.warnings)
            
            success = all(r.success for r in results) and total_errors == 0
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=success,
                message=f"Migration completed with {total_migrated} items migrated, {total_errors} errors",
                migrated_count=total_migrated,
                error_count=total_errors,
                warnings=all_warnings,
                backup_path=backup_path,
                duration_seconds=duration
            )
            
        except Exception as e:
            # If migration fails, attempt rollback
            if backup_path and not dry_run:
                await self._rollback_migration(context, backup_path)
            
            return MigrationResult(
                success=False,
                message=f"Migration failed: {str(e)}",
                error_count=1,
                backup_path=backup_path,
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    async def _migrate_workspace_structure(self, context: MigrationContext) -> MigrationResult:
        """Migrate workspace directory structure."""
        try:
            if context.dry_run:
                return MigrationResult(
                    success=True,
                    message="Workspace structure migration analyzed (dry run)",
                    migrated_count=1
                )
            
            # Create new workspace directory structure
            target_dirs = [
                context.target_path,
                context.target_path / "templates",
                context.target_path / "pipelines", 
                context.target_path / "cache",
                context.target_path / "storage"
            ]
            
            for directory in target_dirs:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Copy existing files from legacy structure
            legacy_dirs_to_copy = {
                "templates": "templates",
                "pipelines": "pipelines",
                "styles": "templates"  # Migrate styles to templates
            }
            
            copied_count = 0
            for legacy_dir, target_dir in legacy_dirs_to_copy.items():
                legacy_path = context.source_path / legacy_dir
                if legacy_path.exists():
                    target_path = context.target_path / target_dir
                    copied_count += await self._copy_directory(legacy_path, target_path)
            
            return MigrationResult(
                success=True,
                message=f"Workspace structure migrated, {copied_count} files copied",
                migrated_count=copied_count
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Workspace structure migration failed: {str(e)}",
                error_count=1
            )
    
    async def _migrate_configuration(self, context: MigrationContext) -> MigrationResult:
        """Migrate workspace configuration to new DDD format."""
        try:
            # Look for legacy config files
            config_files = [
                context.source_path / "config.yaml",
                context.source_path / ".writeit" / "config.yaml",
                context.source_path / "settings.yaml"
            ]
            
            legacy_config = None
            config_source = None
            
            for config_file in config_files:
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        legacy_config = yaml.safe_load(f)
                    config_source = config_file
                    break
            
            if not legacy_config:
                return MigrationResult(
                    success=True,
                    message="No legacy configuration found, using defaults",
                    migrated_count=0
                )
            
            if context.dry_run:
                return MigrationResult(
                    success=True,
                    message=f"Configuration migration analyzed (dry run) from {config_source}",
                    migrated_count=1
                )
            
            # Create new DDD workspace configuration
            workspace_config = WorkspaceConfiguration.default()
            
            # Migrate known configuration keys
            migration_map = {
                "default_model": "default_model",
                "model_preference": "default_model", 
                "cache_enabled": "enable_cache",
                "cache_ttl_hours": "cache_ttl_hours",
                "max_cache_entries": "max_cache_entries"  # This may not exist in target
            }
            
            migrated_keys = 0
            for legacy_key, new_key in migration_map.items():
                if legacy_key in legacy_config:
                    try:
                        workspace_config = workspace_config.set_value(new_key, legacy_config[legacy_key])
                        migrated_keys += 1
                    except KeyError:
                        # Configuration key not defined in schema, skip
                        pass
            
            # Save new configuration
            context.target_path.mkdir(parents=True, exist_ok=True)
            config_path = context.target_path / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(workspace_config.to_dict(), f, default_flow_style=False)
            
            return MigrationResult(
                success=True,
                message=f"Configuration migrated from {config_source}, {migrated_keys} keys updated",
                migrated_count=migrated_keys
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Configuration migration failed: {str(e)}",
                error_count=1
            )
    
    async def _migrate_token_usage(self, context: MigrationContext) -> MigrationResult:
        """Migrate legacy token usage data to new TokenUsage entities."""
        try:
            # Look for legacy token usage data
            legacy_token_files = [
                context.source_path / "token_usage.json",
                context.source_path / "usage_data.json",
                context.source_path / ".writeit" / "token_usage.json"
            ]
            
            migrated_count = 0
            warnings = []
            
            for token_file in legacy_token_files:
                if not token_file.exists():
                    continue
                
                with open(token_file, 'r') as f:
                    legacy_data = json.load(f)
                
                if context.dry_run:
                    migrated_count += len(legacy_data.get('runs', []))
                    warnings.append(f"Found {len(legacy_data.get('runs', []))} legacy token records")
                    continue
                
                # Create storage adapter for new workspace
                storage = create_storage_adapter(context.target_path / "storage")
                
                # Migrate each token usage record
                for run_data in legacy_data.get('runs', []):
                    try:
                        # Convert legacy PipelineRunTokens to new TokenUsage entities
                        for step_data in run_data.get('steps', []):
                            token_usage = self._convert_legacy_step_usage(
                                step_data, 
                                run_data.get('pipeline_name', 'unknown'),
                                context.workspace_name
                            )
                            
                            # Store using new repository pattern
                            await storage.store_json(
                                f"token_usage/{token_usage.id}",
                                token_usage.to_analytics_dict(),
                                db_name="token_usage"
                            )
                            migrated_count += 1
                            
                    except Exception as e:
                        warnings.append(f"Failed to migrate step usage: {str(e)}")
            
            return MigrationResult(
                success=True,
                message=f"Token usage migration completed, {migrated_count} records migrated",
                migrated_count=migrated_count,
                warnings=warnings
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Token usage migration failed: {str(e)}",
                error_count=1
            )
    
    async def _migrate_cache(self, context: MigrationContext) -> MigrationResult:
        """Migrate legacy cache data to new cache structure."""
        try:
            # Look for LMDB cache files
            cache_files = list(context.source_path.glob("*.mdb")) + \
                         list(context.source_path.glob("*.lmdb")) + \
                         list((context.source_path / ".writeit").glob("*.mdb"))
            
            if not cache_files:
                return MigrationResult(
                    success=True,
                    message="No legacy cache files found",
                    migrated_count=0
                )
            
            if context.dry_run:
                return MigrationResult(
                    success=True,
                    message=f"Found {len(cache_files)} legacy cache files to migrate",
                    migrated_count=len(cache_files)
                )
            
            migrated_count = 0
            warnings = []
            
            # Create new cache storage
            storage = create_storage_adapter(context.target_path / "storage")
            
            for cache_file in cache_files:
                try:
                    # Open legacy LMDB database
                    env = lmdb.open(str(cache_file), readonly=True, max_dbs=5)
                    
                    with env.begin() as txn:
                        # Get all cache keys
                        cursor = txn.cursor()
                        cache_keys = []
                        for key, value in cursor:
                            cache_keys.append((key, value))
                    
                    env.close()
                    
                    # Migrate cache entries to new format
                    for key, value in cache_keys:
                        try:
                            # Parse legacy cache entry
                            legacy_entry = json.loads(value.decode('utf-8'))
                            
                            # Convert to new cache format
                            new_entry = self._convert_legacy_cache_entry(legacy_entry)
                            
                            # Store in new cache structure
                            await storage.store_json(
                                f"llm_cache/{new_entry['cache_key']}",
                                new_entry,
                                db_name="llm_cache"
                            )
                            migrated_count += 1
                            
                        except Exception as e:
                            warnings.append(f"Failed to migrate cache entry {key}: {str(e)}")
                    
                except Exception as e:
                    warnings.append(f"Failed to process cache file {cache_file}: {str(e)}")
            
            return MigrationResult(
                success=True,
                message=f"Cache migration completed, {migrated_count} entries migrated",
                migrated_count=migrated_count,
                warnings=warnings
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Cache migration failed: {str(e)}",
                error_count=1
            )
    
    async def _migrate_pipelines_and_templates(self, context: MigrationContext) -> MigrationResult:
        """Migrate pipeline and template data to new DDD entities."""
        try:
            migrated_count = 0
            warnings = []
            
            # Migrate pipeline templates
            pipeline_dirs = [
                context.source_path / "pipelines",
                context.source_path / ".writeit" / "pipelines"
            ]
            
            for pipeline_dir in pipeline_dirs:
                if not pipeline_dir.exists():
                    continue
                
                for pipeline_file in pipeline_dir.glob("*.yaml"):
                    try:
                        with open(pipeline_file, 'r') as f:
                            pipeline_data = yaml.safe_load(f)
                        
                        if context.dry_run:
                            migrated_count += 1
                            continue
                        
                        # Convert to new pipeline template format
                        pipeline_template = self._convert_legacy_pipeline(pipeline_data)
                        
                        # Store in new format
                        from dataclasses import asdict
                        target_path = context.target_path / "pipelines" / pipeline_file.name
                        with open(target_path, 'w') as f:
                            yaml.dump(asdict(pipeline_template), f, default_flow_style=False)
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        warnings.append(f"Failed to migrate pipeline {pipeline_file}: {str(e)}")
            
            # Migrate style templates
            style_dirs = [
                context.source_path / "styles",
                context.source_path / ".writeit" / "styles"
            ]
            
            for style_dir in style_dirs:
                if not style_dir.exists():
                    continue
                
                for style_file in style_dir.glob("*.yaml"):
                    try:
                        with open(style_file, 'r') as f:
                            style_data = yaml.safe_load(f)
                        
                        if context.dry_run:
                            migrated_count += 1
                            continue
                        
                        # Convert to new template format
                        template = self._convert_legacy_style_template(style_data)
                        
                        # Store in new format
                        from dataclasses import asdict
                        target_path = context.target_path / "templates" / style_file.name
                        with open(target_path, 'w') as f:
                            yaml.dump(asdict(template), f, default_flow_style=False)
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        warnings.append(f"Failed to migrate style template {style_file}: {str(e)}")
            
            return MigrationResult(
                success=True,
                message=f"Pipelines and templates migration completed, {migrated_count} files migrated",
                migrated_count=migrated_count,
                warnings=warnings
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Pipelines and templates migration failed: {str(e)}",
                error_count=1
            )
    
    def _convert_legacy_step_usage(self, step_data: Dict[str, Any], pipeline_name: str, workspace_name: str) -> TokenUsage:
        """Convert legacy step token usage to new TokenUsage entity."""
        
        usage_data = step_data.get('usage', {})
        
        # Create token metrics
        metrics = TokenMetrics(
            input_tokens=usage_data.get('input_tokens', 0),
            output_tokens=usage_data.get('output_tokens', 0),
            total_tokens=usage_data.get('total_tokens', 0),
            cached_tokens=usage_data.get('cached_tokens', 0)
        )
        
        # Create cost breakdown (estimate from legacy data)
        input_cost = Decimal(str(metrics.input_tokens * 0.000002))  # $2 per 1M tokens
        output_cost = Decimal(str(metrics.output_tokens * 0.000010))  # $10 per 1M tokens
        cost_breakdown = CostBreakdown(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost
        )
        
        # Create new TokenUsage entity
        return TokenUsage.create(
            session_id=f"legacy-{pipeline_name}-{uuid.uuid4().hex[:8]}",
            model_name=ModelName(step_data.get('model_name', 'unknown')),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            usage_category=UsageCategory.PIPELINE_EXECUTION,
            workspace_name=workspace_name,
            pipeline_id=pipeline_name,
            step_id=step_data.get('step_key'),
            cached_tokens=metrics.cached_tokens
        ).calculate_cost(
            input_cost / Decimal(str(metrics.input_tokens)) if metrics.input_tokens > 0 else Decimal('0'),
            output_cost / Decimal(str(metrics.output_tokens)) if metrics.output_tokens > 0 else Decimal('0')
        )
    
    def _convert_legacy_cache_entry(self, legacy_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy cache entry to new format."""
        
        return {
            "cache_key": legacy_entry.get('cache_key', f"legacy-{uuid.uuid4().hex[:12]}"),
            "prompt": legacy_entry.get('prompt', ''),
            "model_name": legacy_entry.get('model_name', 'unknown'),
            "response": legacy_entry.get('response', ''),
            "tokens_used": legacy_entry.get('tokens_used', {}),
            "created_at": legacy_entry.get('created_at', datetime.now().isoformat()),
            "accessed_at": legacy_entry.get('accessed_at', datetime.now().isoformat()),
            "access_count": legacy_entry.get('access_count', 1),
            "metadata": {
                **legacy_entry.get('metadata', {}),
                "migrated_from_legacy": True,
                "migration_timestamp": datetime.now().isoformat()
            }
        }
    
    def _convert_legacy_pipeline(self, legacy_data: Dict[str, Any]) -> PipelineTemplate:
        """Convert legacy pipeline to new PipelineTemplate entity."""
        
        # This would need to be implemented based on the exact legacy pipeline format
        # For now, return a basic structure
        return PipelineTemplate(
            id=PipelineId.from_name(legacy_data.get('name', 'legacy-pipeline')),
            name=legacy_data.get('name', 'Legacy Pipeline'),
            description=legacy_data.get('description', 'Migrated from legacy format'),
            version=legacy_data.get('version', '1.0.0'),
            steps={},  # Would need to convert legacy steps
            metadata={
                **legacy_data.get('metadata', {}),
                "migrated_from_legacy": True
            }
        )
    
    def _convert_legacy_style_template(self, legacy_data: Dict[str, Any]) -> Template:
        """Convert legacy style template to new Template entity."""
        
        # Create basic template - would need more sophisticated conversion
        yaml_content = yaml.dump(legacy_data, default_flow_style=False)
        return Template.create(
            name=TemplateName.from_user_input(legacy_data.get('name', 'legacy-style')),
            content_type=ContentType.documentation(),  # Use generic type for style templates
            yaml_content=yaml_content,
            description=legacy_data.get('description', 'Migrated from legacy format'),
            author="migration-service",
            metadata={
                **legacy_data.get('metadata', {}),
                "migrated_from_legacy": True
            }
        )
    
    async def _create_backup(self, source_path: Path, workspace_name: str) -> Path:
        """Create backup of source workspace."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"migration_backup_{workspace_name}_{timestamp}"
        backup_path = Path.home() / ".writeit" / "backups" / backup_name
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy entire directory
        shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
        
        return backup_path
    
    async def _copy_directory(self, source: Path, target: Path) -> int:
        """Copy directory contents and return count of copied files."""
        if not source.exists():
            return 0
        
        target.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        for item in source.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(source)
                target_file = target / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_file)
                copied_count += 1
        
        return copied_count
    
    async def _rollback_migration(self, context: MigrationContext, backup_path: Path) -> None:
        """Rollback migration using backup."""
        try:
            if context.target_path.exists():
                shutil.rmtree(context.target_path)
            
            if backup_path.exists():
                shutil.copytree(backup_path, context.target_path)
                
        except Exception as e:
            print(f"Rollback failed: {str(e)}")
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Get comprehensive migration report."""
        return {
            "migration_log": self.migration_log,
            "total_migrations": len(self.migration_log),
            "success_count": sum(1 for log in self.migration_log if log.get('success', False)),
            "error_count": sum(1 for log in self.migration_log if not log.get('success', False)),
            "last_migration": self.migration_log[-1] if self.migration_log else None
        }