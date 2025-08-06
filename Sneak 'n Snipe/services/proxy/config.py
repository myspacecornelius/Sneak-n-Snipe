"""
SneakerSniper Configuration Loader
Loads settings from a YAML file and environment variables.
"""

import yaml
import os
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    "redis_url": "redis://localhost:6379",
    "providers": [],
    "proxy_requirements": {
        "min_health_score": 70,
        "location": "any",
        "type": "any"
    },
    "monitoring": {
        "health_check_interval": 300,
        "cost_monitor_interval": 3600,
        "rotation_interval": 600
    }
}

def load_config(path: str = "config.yml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file and merge with defaults.
    
    Args:
        path: Path to the configuration file.
        
    Returns:
        A dictionary containing the configuration.
    """
    config = DEFAULT_CONFIG.copy()

    # Load from file if it exists
    if os.path.exists(path):
        with open(path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)

    # Override with environment variables
    for key, value in config.items():
        if isinstance(value, dict):
            for sub_key in value:
                env_var = f"SNIPER_{key.upper()}_{sub_key.upper()}"
                if env_var in os.environ:
                    config[key][sub_key] = os.environ[env_var]
        else:
            env_var = f"SNIPER_{key.upper()}"
            if env_var in os.environ:
                config[key] = os.environ[env_var]
                
    return config
