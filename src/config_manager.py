"""Configuration management for GP Consultation Extractor.

This module handles loading and validating configuration from multiple sources:
1. Environment variables (highest priority)
2. YAML configuration file
3. Default values (lowest priority)
"""

import os
import yaml
from typing import Any, Optional, Dict
from pathlib import Path


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""
    pass


class ConfigManager:
    """Manages application configuration from multiple sources."""
    
    DEFAULT_CONFIG = {
        'llm': {
            'provider': 'gemini',
            'gemini': {
                'model': 'gemini-2.5-pro'
            },
            'bedrock': {
                'region': 'us-east-1',
                'model_id': 'anthropic.claude-sonnet-4-5-20250929-v1:0'
            }
        },
        'extraction': {
            'confidence_threshold': 0.7,
            'retry_attempts': 1,
            'batch_size': 10
        },
        'output': {
            'directory': '/output',
            'csv_encoding': 'utf-8'
        },
        'logging': {
            'level': 'INFO',
            'format': 'json'
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to YAML configuration file. If None, uses default config.
        """
        self.config = self._load_config(config_file)
        self._apply_env_overrides()
    
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file or use defaults.
        
        Args:
            config_file: Path to YAML configuration file
            
        Returns:
            Configuration dictionary
        """
        # Start with default config
        config = self.DEFAULT_CONFIG.copy()
        
        # Load from file if provided
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config = self._deep_merge(config, file_config)
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Dictionary with override values
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # LLM provider settings
        if os.getenv('AWS_BEDROCK_ENABLED', '').lower() == 'true':
            self.config['llm']['provider'] = 'bedrock'
        
        if os.getenv('LANGEXTRACT_API_KEY'):
            self.config['llm']['gemini']['api_key'] = os.getenv('LANGEXTRACT_API_KEY')
        
        # AWS Bedrock - Custom API Gateway endpoint
        if os.getenv('BEDROCK_API_ENDPOINT'):
            if 'bedrock' not in self.config['llm']:
                self.config['llm']['bedrock'] = {}
            self.config['llm']['bedrock']['api_endpoint'] = os.getenv('BEDROCK_API_ENDPOINT')
            self.config['llm']['bedrock']['use_custom_endpoint'] = True
        
        if os.getenv('BEDROCK_API_KEY'):
            if 'bedrock' not in self.config['llm']:
                self.config['llm']['bedrock'] = {}
            self.config['llm']['bedrock']['api_key'] = os.getenv('BEDROCK_API_KEY')
        
        # AWS Bedrock - Standard boto3 credentials (fallback)
        if os.getenv('AWS_ACCESS_KEY_ID'):
            if 'bedrock' not in self.config['llm']:
                self.config['llm']['bedrock'] = {}
            self.config['llm']['bedrock']['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
        
        if os.getenv('AWS_SECRET_ACCESS_KEY'):
            if 'bedrock' not in self.config['llm']:
                self.config['llm']['bedrock'] = {}
            self.config['llm']['bedrock']['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if os.getenv('AWS_REGION'):
            if 'bedrock' not in self.config['llm']:
                self.config['llm']['bedrock'] = {}
            self.config['llm']['bedrock']['region'] = os.getenv('AWS_REGION')
        
        if os.getenv('MODEL_ID'):
            provider = self.config['llm']['provider']
            if provider == 'bedrock':
                self.config['llm']['bedrock']['model_id'] = os.getenv('MODEL_ID')
            else:
                self.config['llm']['gemini']['model'] = os.getenv('MODEL_ID')
        
        # Extraction settings
        if os.getenv('EXTRACTION_CONFIDENCE_THRESHOLD'):
            try:
                threshold = float(os.getenv('EXTRACTION_CONFIDENCE_THRESHOLD'))
                self.config['extraction']['confidence_threshold'] = threshold
            except ValueError:
                pass
        
        # Output settings
        if os.getenv('OUTPUT_DIR'):
            self.config['output']['directory'] = os.getenv('OUTPUT_DIR')
        
        # Logging settings
        if os.getenv('LOG_LEVEL'):
            self.config['logging']['level'] = os.getenv('LOG_LEVEL')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'llm.provider')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config.get('llm.provider')
            'gemini'
            >>> config.get('extraction.confidence_threshold')
            0.7
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate(self) -> bool:
        """Validate that required configuration is present.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        provider = self.get('llm.provider')
        
        if provider == 'gemini':
            api_key = self.get('llm.gemini.api_key')
            if not api_key:
                raise ConfigurationError(
                    "LANGEXTRACT_API_KEY environment variable is required for Gemini provider"
                )
        elif provider == 'bedrock':
            region = self.get('llm.bedrock.region')
            if not region:
                raise ConfigurationError(
                    "AWS_REGION environment variable is required for Bedrock provider"
                )
        else:
            raise ConfigurationError(
                f"Invalid LLM provider: {provider}. Must be 'gemini' or 'bedrock'"
            )
        
        # Validate output directory
        output_dir = self.get('output.directory')
        if not output_dir:
            raise ConfigurationError("Output directory must be configured")
        
        return True
