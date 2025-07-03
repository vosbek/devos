"""
Configuration management for DevOS daemon
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """DevOS daemon configuration"""
    
    # API Configuration
    api_host: str = "127.0.0.1"
    api_port: int = 8080
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key: str = ""
    aws_secret_key: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/var/log/devos/daemon.log"
    
    # File System Monitoring
    watch_paths: List[str] = field(default_factory=lambda: ["/home", "/opt", "/tmp"])
    
    # Process Monitoring
    process_update_interval: int = 30
    
    # Git Repository Paths
    git_repo_paths: List[str] = field(default_factory=lambda: ["/home"])
    
    # Model Configuration
    model_config: Dict[str, Any] = field(default_factory=lambda: {
        "default_model": "claude-3-haiku",
        "cost_threshold": 0.10,
        "timeout": 30
    })
    
    # Approval Configuration
    approval_config: Dict[str, Any] = field(default_factory=lambda: {
        "auto_approve_safe": True,
        "approval_timeout": 300,
        "learn_preferences": True
    })
    
    # Security Configuration
    security_config: Dict[str, Any] = field(default_factory=lambda: {
        "sandbox_enabled": True,
        "max_execution_time": 120,
        "allowed_commands": [
            "ls", "cp", "mv", "mkdir", "git", "npm", "pip", "docker"
        ],
        "blocked_commands": [
            "rm -rf /", "mkfs", "dd"
        ]
    })
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file"""
        
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Create default config
            default_config = cls()
            default_config.save_to_file(config_path)
            return default_config
        
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Create config object with loaded data
            config = cls()
            
            # Update fields from loaded data
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            return config
            
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            print("Using default configuration")
            return cls()
    
    def save_to_file(self, config_path: str):
        """Save configuration to YAML file"""
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for YAML serialization
        config_dict = {
            'api_host': self.api_host,
            'api_port': self.api_port,
            'aws_region': self.aws_region,
            'aws_access_key': self.aws_access_key,
            'aws_secret_key': self.aws_secret_key,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'watch_paths': self.watch_paths,
            'process_update_interval': self.process_update_interval,
            'git_repo_paths': self.git_repo_paths,
            'model_config': self.model_config,
            'approval_config': self.approval_config,
            'security_config': self.security_config
        }
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        
        errors = []
        
        # Validate AWS credentials
        if not self.aws_access_key:
            errors.append("AWS access key is required")
        if not self.aws_secret_key:
            errors.append("AWS secret key is required")
        
        # Validate API configuration
        if not (1024 <= self.api_port <= 65535):
            errors.append("API port must be between 1024 and 65535")
        
        # Validate paths
        for path in self.watch_paths:
            if not Path(path).exists():
                errors.append(f"Watch path does not exist: {path}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {self.log_level}")
        
        return errors