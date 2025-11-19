"""Configuration management for GP Consultation Extractor.

This module handles loading and validating configuration from multiple sources:
1. Environment variables (highest priority)
2. YAML configuration file
3. Default values (lowest priority)
"""

import os
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""


class ConfigManager:
    """Manages application configuration from multiple sources."""

    DEFAULT_CONFIG = {
        "llm": {
            "provider": "gemini",
            "gemini": {"model": "gemini-2.5-pro"},
            "bedrock": {
                "region": "us-east-1",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
            },
        },
        "extraction": {"confidence_threshold": 0.7, "retry_attempts": 1, "batch_size": 10},
        "output": {"directory": "/output", "csv_encoding": "utf-8"},
        "logging": {"level": "INFO", "format": "json"},
    }

    def __init__(self, config_file: str | None = None):
        """Initialize configuration manager.

        Args:
            config_file: Path to YAML configuration file. If None, uses default config.
        """
        # Load .env file if available
        if DOTENV_AVAILABLE:
            # Try to load .env from current directory or project root
            env_path = Path(".env")
            if not env_path.exists():
                env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)

        self.config = self._load_config(config_file)
        self._apply_env_overrides()

    def _load_config(self, config_file: str | None) -> dict:
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
            with open(config_file, encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config = self._deep_merge(config, file_config)

        return config

    def _deep_merge(self, base: dict, override: dict) -> dict:
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
        self._apply_provider_overrides()
        self._apply_bedrock_overrides()
        self._apply_extraction_overrides()
        self._apply_output_overrides()
        self._apply_logging_overrides()

    def _apply_provider_overrides(self):
        """Override provider-specific settings from env."""
        if os.getenv("AWS_BEDROCK_ENABLED", "").lower() == "true":
            self.config["llm"]["provider"] = "bedrock"

        gemini_api_key = os.getenv("LANGEXTRACT_API_KEY")
        if gemini_api_key:
            self.config["llm"]["gemini"]["api_key"] = gemini_api_key

        model_id = os.getenv("MODEL_ID")
        if model_id:
            provider = self.config["llm"]["provider"]
            target_key = "bedrock" if provider == "bedrock" else "gemini"
            self.config["llm"][target_key]["model" if target_key == "gemini" else "model_id"] = (
                model_id
            )

    def _apply_bedrock_overrides(self):
        """Apply Bedrock-specific overrides."""
        bedrock_config = self._ensure_bedrock_config()

        api_endpoint = os.getenv("BEDROCK_API_ENDPOINT")
        if api_endpoint:
            bedrock_config["api_endpoint"] = api_endpoint
            bedrock_config["use_custom_endpoint"] = True

        api_key = os.getenv("BEDROCK_API_KEY")
        if api_key:
            bedrock_config["api_key"] = api_key

        team_id = os.getenv("BEDROCK_TEAM_ID")
        if team_id:
            bedrock_config["team_id"] = team_id

        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        if aws_access_key:
            bedrock_config["aws_access_key_id"] = aws_access_key

        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        if aws_secret:
            bedrock_config["aws_secret_access_key"] = aws_secret

        aws_region = os.getenv("AWS_REGION")
        if aws_region:
            bedrock_config["region"] = aws_region

    def _apply_extraction_overrides(self):
        """Override extraction-related settings."""
        threshold_env = os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD")
        if not threshold_env:
            return
        try:
            threshold = float(threshold_env)
        except ValueError:
            return
        self.config["extraction"]["confidence_threshold"] = threshold

    def _apply_output_overrides(self):
        """Override output settings."""
        output_dir = os.getenv("OUTPUT_DIR")
        if output_dir:
            self.config["output"]["directory"] = output_dir

    def _apply_logging_overrides(self):
        """Override logging settings."""
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            self.config["logging"]["level"] = log_level

    def _ensure_bedrock_config(self) -> dict:
        """Ensure bedrock config dictionary exists."""
        bedrock_config = self.config["llm"].get("bedrock")
        if bedrock_config is None:
            bedrock_config = {}
            self.config["llm"]["bedrock"] = bedrock_config
        return bedrock_config

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
        keys = key.split(".")
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
        provider = self.get("llm.provider")

        if provider == "gemini":
            api_key = self.get("llm.gemini.api_key")
            if not api_key:
                raise ConfigurationError(
                    "LANGEXTRACT_API_KEY environment variable is required for Gemini provider"
                )
        elif provider == "bedrock":
            region = self.get("llm.bedrock.region")
            if not region:
                raise ConfigurationError(
                    "AWS_REGION environment variable is required for Bedrock provider"
                )
        else:
            raise ConfigurationError(
                f"Invalid LLM provider: {provider}. Must be 'gemini' or 'bedrock'"
            )

        # Validate output directory
        output_dir = self.get("output.directory")
        if not output_dir:
            raise ConfigurationError("Output directory must be configured")

        return True
