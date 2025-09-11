"""
Documentation extractors for different source types
"""

from .api import APIExtractor
from .modules import ModuleExtractor
from .cli import CLIExtractor
from .templates import TemplateExtractor
from .examples import ExampleExtractor

__all__ = [
    "APIExtractor",
    "ModuleExtractor",
    "CLIExtractor",
    "TemplateExtractor",
    "ExampleExtractor",
]
