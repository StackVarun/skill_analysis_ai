"""Re-export config for convenience."""
import os
import sys

_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig, config_by_name

__all__ = ["Config", "DevelopmentConfig", "TestingConfig", "ProductionConfig", "config_by_name"]
