#!/usr/bin/env python3

import json
import os
import logging
from typing import Dict, Any, Optional

class ConfigLoader:
    """Load and manage configuration for the VirtualBox-Whonix MCP server."""
    
    def __init__(self, config_path: str = None):
        """Initialize with optional config file path."""
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config.json"
        )
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from a JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default configuration
                return self._default_config()
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "virtualbox": {
                "vboxmanage_path": "/usr/bin/VBoxManage",
                "default_start_type": "headless"
            },
            "whonix": {
                "gateway_vm": "Whonix-Gateway-Xfce",
                "workstation_vm": "Whonix-Workstation-Xfce",
                "default_username": "user",
                "default_password": os.getenv("WHONIX_VM_PASSWORD", "")
            },
            "tor": {
                "socks_port": 9050,
                "control_port": 9051,
                "allow_new_identity": True,
                "check_exit_node": True
            },
            "logging": {
                "level": "INFO",
                "log_file": "vbox_whonix_server.log",
                "max_size": 10485760,
                "backup_count": 3
            }
        }
    
    def _setup_logging(self) -> None:
        """Configure logging based on settings."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("log_file", "vbox_whonix_server.log")
        
        try:
            from logging.handlers import RotatingFileHandler
            
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configure rotating file handler
            handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config.get("max_size", 10485760),
                backupCount=log_config.get("backup_count", 3)
            )
            
            # Configure logging format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            root_logger.addHandler(handler)
            
            # Also add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            
            logging.info("Logging initialized")
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value, with optional default."""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def save(self) -> bool:
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
            return False
    
    def update(self, section: str, key: str, value: Any) -> None:
        """Update a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
