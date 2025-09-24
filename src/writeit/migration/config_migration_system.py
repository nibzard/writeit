"""Configuration Migration System for WriteIt DDD Refactoring.

This module provides comprehensive configuration migration utilities for converting
legacy configuration formats to the new DDD-compatible structure. It handles:
- Global configuration migration
- Workspace-specific configuration migration
- Environment variable configuration
- LLM provider configuration migration
- Template and style configuration migration
"""

import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import uuid

from writeit.workspace.workspace import Workspace


class ConfigMigrationError(Exception):
    """Exception raised during configuration migration."""
    pass


class ConfigMigrationSystem:
    """Handles migration of configuration data to DDD format."""
    
    def __init__(self, workspace: Workspace):
        """Initialize configuration migration system.
        
        Args:
            workspace: Workspace instance
        """
        self.workspace = workspace
        self.migration_log = []
        self.config_cache = {}
        
    def log_migration(self, message: str, level: str = "info") -> None:
        """Log configuration migration activity."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.migration_log.append(log_entry)
        print(f"[{timestamp}] {level.upper()}: {message}")
        
    def get_migration_log(self) -> List[Dict[str, Any]]:
        """Get migration log.
        
        Returns:
            List of migration log entries
        """
        return self.migration_log
        
    def migrate_global_config(self) -> bool:
        """Migrate global configuration to DDD format.
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.log_migration("Starting global configuration migration")
            
            # Load current global config
            global_config_path = self.workspace.base_dir / "config.yaml"
            
            if not global_config_path.exists():
                self.log_migration("No global config found, creating default", "warning")
                return self._create_default_global_config()
                
            # Load existing config
            with open(global_config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
                
            # Migrate to DDD format
            migrated_config = self._migrate_config_to_ddd_format(current_config, "global")
            
            # Write migrated config
            with open(global_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(migrated_config, f, default_flow_style=False, allow_unicode=True)
                
            self.log_migration("Global configuration migration completed successfully")
            return True
            
        except Exception as e:
            self.log_migration(f"Global config migration failed: {e}", "error")
            return False
            
    def migrate_workspace_configs(self, workspace_name: Optional[str] = None) -> bool:
        """Migrate workspace configurations to DDD format.
        
        Args:
            workspace_name: Specific workspace to migrate (None for all)
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            if workspace_name:
                workspace_names = [workspace_name]
            else:
                workspace_names = self.workspace.list_workspaces()
                
            if not workspace_names:
                self.log_migration("No workspaces found for configuration migration", "warning")
                return True
                
            success_count = 0
            for ws_name in workspace_names:
                if self._migrate_single_workspace_config(ws_name):
                    success_count += 1
                    
            result = success_count == len(workspace_names)
            if result:
                self.log_migration(f"Successfully migrated {success_count} workspace configurations")
            else:
                self.log_migration(f"Migrated {success_count}/{len(workspace_names)} workspace configurations", "warning")
                
            return result
            
        except Exception as e:
            self.log_migration(f"Workspace config migration failed: {e}", "error")
            return False
            
    def _migrate_single_workspace_config(self, workspace_name: str) -> bool:
        """Migrate a single workspace configuration.
        
        Args:
            workspace_name: Name of workspace
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            config_path = workspace_path / "workspace.yaml"
            
            if not config_path.exists():
                self.log_migration(f"No config found for workspace {workspace_name}, creating default", "warning")
                return self._create_default_workspace_config(workspace_path)
                
            # Load existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
                
            # Migrate to DDD format
            migrated_config = self._migrate_config_to_ddd_format(current_config, "workspace", workspace_name)
            
            # Write migrated config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(migrated_config, f, default_flow_style=False, allow_unicode=True)
                
            self.log_migration(f"Successfully migrated config for workspace: {workspace_name}")
            return True
            
        except Exception as e:
            self.log_migration(f"Failed to migrate config for workspace {workspace_name}: {e}", "error")
            return False
            
    def _migrate_config_to_ddd_format(self, config: Dict[str, Any], config_type: str, workspace_name: Optional[str] = None) -> Dict[str, Any]:
        """Migrate configuration to DDD format.
        
        Args:
            config: Current configuration
            config_type: Type of configuration ('global' or 'workspace')
            workspace_name: Workspace name (for workspace configs)
            
        Returns:
            Migrated configuration
        """
        migrated = {
            "version": "2.0.0",
            "config_type": config_type,
            "migrated_at": datetime.now().isoformat(),
            "migration_info": {
                "from_version": config.get("writeit_version", "1.0.0"),
                "migration_version": "2.0.0",
                "migrated_by": "writeit-ddd-migration"
            }
        }
        
        if config_type == "global":
            migrated.update(self._migrate_global_config_structure(config))
        else:
            migrated.update(self._migrate_workspace_config_structure(config, workspace_name))
            
        return migrated
        
    def _migrate_global_config_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate global configuration structure.
        
        Args:
            config: Current global configuration
            
        Returns:
            Migrated global configuration structure
        """
        migrated = {
            "global_settings": {
                "default_model": config.get("default_model", "gpt-4o-mini"),
                "auto_save": config.get("auto_save", True),
                "max_history": config.get("max_history", 1000),
                "debug_mode": config.get("debug_mode", False),
                "ui_theme": config.get("ui_theme", "default"),
                "log_level": config.get("log_level", "INFO")
            },
            "workspace_management": {
                "default_workspace": config.get("active_workspace", "default"),
                "workspace_root": str(self.workspace.base_dir),
                "auto_create_workspace": config.get("auto_create_workspace", True)
            },
            "llm_providers": self._migrate_llm_provider_config(config.get("llm_providers", {})),
            "storage": {
                "cache_enabled": config.get("cache_enabled", True),
                "cache_ttl": config.get("cache_ttl", 3600),
                "storage_backend": config.get("storage_backend", "lmdb"),
                "backup_enabled": config.get("backup_enabled", True),
                "backup_interval": config.get("backup_interval", "daily")
            },
            "domains": {
                "pipeline": {
                    "default_execution_mode": config.get("execution_mode", "sequential"),
                    "max_parallel_steps": config.get("max_parallel_steps", 3),
                    "step_timeout": config.get("step_timeout", 300)
                },
                "workspace": {
                    "isolation_enabled": True,
                    "shared_resources": config.get("shared_resources", [])
                },
                "llm": {
                    "default_temperature": config.get("temperature", 0.7),
                    "default_max_tokens": config.get("max_tokens", 1000),
                    "retry_attempts": config.get("retry_attempts", 3)
                }
            }
        }
        
        # Preserve any additional settings
        additional_settings = {k: v for k, v in config.items() 
                             if k not in ["writeit_version", "active_workspace", "workspaces"] and 
                             not self._is_migrated_setting(k)}
        
        if additional_settings:
            migrated["additional_settings"] = additional_settings
            
        return migrated
        
    def _migrate_workspace_config_structure(self, config: Dict[str, Any], workspace_name: Optional[str]) -> Dict[str, Any]:
        """Migrate workspace configuration structure.
        
        Args:
            config: Current workspace configuration
            workspace_name: Workspace name
            
        Returns:
            Migrated workspace configuration structure
        """
        migrated = {
            "workspace_info": {
                "name": workspace_name or config.get("name", "default"),
                "display_name": config.get("display_name", workspace_name or "Default Workspace"),
                "description": config.get("description", ""),
                "created_at": config.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat()
            },
            "workspace_settings": {
                "default_model": config.get("default_model", "gpt-4o-mini"),
                "auto_save": config.get("auto_save", True),
                "max_history": config.get("max_history", 1000),
                "ui_theme": config.get("ui_theme", "default")
            },
            "llm_configuration": self._migrate_workspace_llm_config(config.get("llm_providers", {})),
            "template_settings": {
                "default_template": config.get("default_pipeline"),
                "template_validation": config.get("template_validation", True),
                "auto_load_templates": config.get("auto_load_templates", True)
            },
            "domain_settings": {
                "pipeline": {
                    "execution_mode": config.get("execution_mode", "sequential"),
                    "max_parallel_steps": config.get("max_parallel_steps", 3),
                    "step_timeout": config.get("step_timeout", 300)
                },
                "workspace": {
                    "isolation_enabled": True,
                    "cache_enabled": config.get("cache_enabled", True),
                    "storage_backend": config.get("storage_backend", "lmdb")
                },
                "llm": {
                    "default_temperature": config.get("temperature", 0.7),
                    "default_max_tokens": config.get("max_tokens", 1000),
                    "retry_attempts": config.get("retry_attempts", 3)
                }
            },
            "structure": {
                "version": "2.0",
                "ddd_compatible": True,
                "paths": {
                    "pipelines": "pipelines",
                    "workspace_data": "workspace/data",
                    "domains": "domains",
                    "storage": "storage",
                    "templates": "templates",
                    "styles": "styles",
                    "articles": "articles",
                    "cache": "workspace/cache",
                    "logs": "logs"
                }
            }
        }
        
        # Preserve any additional settings
        additional_settings = {k: v for k, v in config.items() 
                             if not self._is_migrated_setting(k)}
        
        if additional_settings:
            migrated["additional_settings"] = additional_settings
            
        return migrated
        
    def _migrate_llm_provider_config(self, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate LLM provider configuration.
        
        Args:
            llm_config: Current LLM provider configuration
            
        Returns:
            Migrated LLM provider configuration
        """
        migrated = {
            "providers": {},
            "defaults": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "settings": {
                "cache_enabled": True,
                "cache_ttl": 3600,
                "retry_attempts": 3,
                "timeout": 30
            }
        }
        
        # Migrate provider configurations
        for provider_name, provider_config in llm_config.items():
            if isinstance(provider_config, dict):
                migrated["providers"][provider_name] = {
                    "api_key": provider_config.get("api_key"),
                    "base_url": provider_config.get("base_url"),
                    "models": provider_config.get("models", []),
                    "default_model": provider_config.get("default_model"),
                    "settings": provider_config.get("settings", {})
                }
            else:
                # Simple string configuration
                migrated["providers"][provider_name] = {
                    "api_key": provider_config,
                    "models": [],
                    "settings": {}
                }
                
        return migrated
        
    def _migrate_workspace_llm_config(self, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate workspace-specific LLM configuration.
        
        Args:
            llm_config: Current workspace LLM configuration
            
        Returns:
            Migrated workspace LLM configuration
        """
        migrated = {
            "provider_overrides": {},
            "model_overrides": {},
            "settings": {
                "temperature": llm_config.get("temperature", 0.7),
                "max_tokens": llm_config.get("max_tokens", 1000),
                "top_p": llm_config.get("top_p", 1.0),
                "frequency_penalty": llm_config.get("frequency_penalty", 0.0),
                "presence_penalty": llm_config.get("presence_penalty", 0.0)
            }
        }
        
        # Migrate provider overrides
        for provider_name, provider_config in llm_config.items():
            if isinstance(provider_config, dict):
                migrated["provider_overrides"][provider_name] = {
                    "api_key": provider_config.get("api_key"),
                    "base_url": provider_config.get("base_url"),
                    "enabled": provider_config.get("enabled", True)
                }
                
                # Migrate model overrides
                if "models" in provider_config:
                    for model_name, model_config in provider_config["models"].items():
                        if isinstance(model_config, dict):
                            migrated["model_overrides"][model_name] = {
                                "provider": provider_name,
                                "settings": model_config
                            }
                        else:
                            migrated["model_overrides"][model_name] = {
                                "provider": provider_name,
                                "settings": {}
                            }
                            
        return migrated
        
    def _is_migrated_setting(self, setting_name: str) -> bool:
        """Check if a setting has been migrated to new structure.
        
        Args:
            setting_name: Name of the setting
            
        Returns:
            True if setting has been migrated, False otherwise
        """
        migrated_settings = {
            # Global settings
            "writeit_version", "active_workspace", "workspaces",
            "default_model", "auto_save", "max_history", "debug_mode",
            "ui_theme", "log_level", "auto_create_workspace", "cache_enabled",
            "cache_ttl", "storage_backend", "backup_enabled", "backup_interval",
            "execution_mode", "max_parallel_steps", "step_timeout", "temperature",
            "max_tokens", "retry_attempts", "shared_resources",
            
            # Workspace settings
            "name", "display_name", "description", "created_at", "default_pipeline",
            "template_validation", "auto_load_templates", "cache_enabled", "storage_backend"
        }
        
        return setting_name in migrated_settings
        
    def _create_default_global_config(self) -> bool:
        """Create default global configuration.
        
        Returns:
            True if creation successful, False otherwise
        """
        try:
            default_config = {
                "version": "2.0.0",
                "config_type": "global",
                "migrated_at": datetime.now().isoformat(),
                "migration_info": {
                    "from_version": "none",
                    "migration_version": "2.0.0",
                    "migrated_by": "writeit-ddd-migration"
                },
                "global_settings": {
                    "default_model": "gpt-4o-mini",
                    "auto_save": True,
                    "max_history": 1000,
                    "debug_mode": False,
                    "ui_theme": "default",
                    "log_level": "INFO"
                },
                "workspace_management": {
                    "default_workspace": "default",
                    "workspace_root": str(self.workspace.base_dir),
                    "auto_create_workspace": True
                },
                "llm_providers": {
                    "providers": {},
                    "defaults": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    "settings": {
                        "cache_enabled": True,
                        "cache_ttl": 3600,
                        "retry_attempts": 3,
                        "timeout": 30
                    }
                },
                "storage": {
                    "cache_enabled": True,
                    "cache_ttl": 3600,
                    "storage_backend": "lmdb",
                    "backup_enabled": True,
                    "backup_interval": "daily"
                },
                "domains": {
                    "pipeline": {
                        "default_execution_mode": "sequential",
                        "max_parallel_steps": 3,
                        "step_timeout": 300
                    },
                    "workspace": {
                        "isolation_enabled": True,
                        "shared_resources": []
                    },
                    "llm": {
                        "default_temperature": 0.7,
                        "default_max_tokens": 1000,
                        "retry_attempts": 3
                    }
                }
            }
            
            config_path = self.workspace.base_dir / "config.yaml"
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
                
            self.log_migration("Created default global configuration")
            return True
            
        except Exception as e:
            self.log_migration(f"Failed to create default global config: {e}", "error")
            return False
            
    def _create_default_workspace_config(self, workspace_path: Path) -> bool:
        """Create default workspace configuration.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            workspace_name = workspace_path.name
            default_config = {
                "version": "2.0.0",
                "config_type": "workspace",
                "migrated_at": datetime.now().isoformat(),
                "migration_info": {
                    "from_version": "none",
                    "migration_version": "2.0.0",
                    "migrated_by": "writeit-ddd-migration"
                },
                "workspace_info": {
                    "name": workspace_name,
                    "display_name": workspace_name.title(),
                    "description": f"Default workspace: {workspace_name}",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                "workspace_settings": {
                    "default_model": "gpt-4o-mini",
                    "auto_save": True,
                    "max_history": 1000,
                    "ui_theme": "default"
                },
                "llm_configuration": {
                    "provider_overrides": {},
                    "model_overrides": {},
                    "settings": {
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "top_p": 1.0,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    }
                },
                "template_settings": {
                    "default_template": None,
                    "template_validation": True,
                    "auto_load_templates": True
                },
                "domain_settings": {
                    "pipeline": {
                        "execution_mode": "sequential",
                        "max_parallel_steps": 3,
                        "step_timeout": 300
                    },
                    "workspace": {
                        "isolation_enabled": True,
                        "cache_enabled": True,
                        "storage_backend": "lmdb"
                    },
                    "llm": {
                        "default_temperature": 0.7,
                        "default_max_tokens": 1000,
                        "retry_attempts": 3
                    }
                },
                "structure": {
                    "version": "2.0",
                    "ddd_compatible": True,
                    "paths": {
                        "pipelines": "pipelines",
                        "workspace_data": "workspace/data",
                        "domains": "domains",
                        "storage": "storage",
                        "templates": "templates",
                        "styles": "styles",
                        "articles": "articles",
                        "cache": "workspace/cache",
                        "logs": "logs"
                    }
                }
            }
            
            config_path = workspace_path / "workspace.yaml"
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
                
            self.log_migration(f"Created default workspace config for: {workspace_name}")
            return True
            
        except Exception as e:
            self.log_migration(f"Failed to create default workspace config: {e}", "error")
            return False
            
    def validate_migrated_configs(self) -> Dict[str, List[str]]:
        """Validate all migrated configurations.
        
        Returns:
            Dictionary mapping config names to validation issues
        """
        validation_results = {}
        
        # Validate global config
        global_config_path = self.workspace.base_dir / "config.yaml"
        if global_config_path.exists():
            issues = self._validate_config_file(global_config_path, "global")
            if issues:
                validation_results["global"] = issues
                
        # Validate workspace configs
        workspace_names = self.workspace.list_workspaces()
        for workspace_name in workspace_names:
            workspace_path = self.workspace.get_workspace_path(workspace_name)
            config_path = workspace_path / "workspace.yaml"
            
            if config_path.exists():
                issues = self._validate_config_file(config_path, "workspace")
                if issues:
                    validation_results[workspace_name] = issues
                    
        return validation_results
        
    def _validate_config_file(self, config_path: Path, config_type: str) -> List[str]:
        """Validate a configuration file.
        
        Args:
            config_path: Path to configuration file
            config_type: Type of configuration
            
        Returns:
            List of validation issues
        """
        issues = []
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if not config:
                issues.append("Configuration file is empty")
                return issues
                
            # Check version
            if config.get("version") != "2.0.0":
                issues.append("Configuration version is not 2.0.0")
                
            # Check migration info
            migration_info = config.get("migration_info", {})
            if not migration_info.get("migrated_at"):
                issues.append("Configuration missing migration timestamp")
                
            # Check structure based on type
            if config_type == "global":
                required_sections = ["global_settings", "workspace_management", "llm_providers", "storage", "domains"]
            else:
                required_sections = ["workspace_info", "workspace_settings", "llm_configuration", "domain_settings", "structure"]
                
            for section in required_sections:
                if section not in config:
                    issues.append(f"Missing required section: {section}")
                    
        except Exception as e:
            issues.append(f"Cannot read configuration file: {e}")
            
        return issues