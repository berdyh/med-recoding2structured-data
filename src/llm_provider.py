"""LLM provider management for GP Consultation Extractor.

This module manages connections to different LLM providers (Gemini and AWS Bedrock)
and provides a unified interface for credential validation and provider selection.
"""

import os
import boto3
from typing import Dict, Optional
from botocore.exceptions import ClientError, NoCredentialsError


class LLMProviderError(Exception):
    """Raised when LLM provider configuration or connection fails."""
    pass


class LLMProviderManager:
    """Manages LLM provider connections and credentials."""
    
    SUPPORTED_PROVIDERS = ['gemini', 'bedrock']
    
    def __init__(self, config: Dict):
        """Initialize LLM provider manager.
        
        Args:
            config: Configuration dictionary from ConfigManager
            
        Raises:
            LLMProviderError: If provider configuration is invalid
        """
        self.config = config
        self.provider = config.get('provider', 'gemini')
        
        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise LLMProviderError(
                f"Unsupported provider: {self.provider}. "
                f"Must be one of {self.SUPPORTED_PROVIDERS}"
            )
        
        self._bedrock_client = None
    
    def get_provider(self) -> str:
        """Return active provider name.
        
        Returns:
            Provider name ('gemini' or 'bedrock')
        """
        return self.provider
    
    def get_api_credentials(self) -> Dict:
        """Return credentials for active provider.
        
        Returns:
            Dictionary containing provider-specific credentials
            
        Raises:
            LLMProviderError: If credentials are not configured
        """
        if self.provider == 'gemini':
            api_key = self.config.get('gemini', {}).get('api_key')
            if not api_key:
                raise LLMProviderError(
                    "Gemini API key not configured. "
                    "Set LANGEXTRACT_API_KEY environment variable."
                )
            
            return {
                'api_key': api_key,
                'model': self.config.get('gemini', {}).get('model', 'gemini-2.5-pro')
            }
        
        elif self.provider == 'bedrock':
            region = self.config.get('bedrock', {}).get('region', 'us-east-1')
            model_id = self.config.get('bedrock', {}).get(
                'model_id',
                'anthropic.claude-sonnet-4-5-20250929-v1:0'
            )
            
            return {
                'region': region,
                'model_id': model_id
            }
        
        raise LLMProviderError(f"Unknown provider: {self.provider}")
    
    def validate_credentials(self) -> bool:
        """Verify credentials are valid for the active provider.
        
        Returns:
            True if credentials are valid
            
        Raises:
            LLMProviderError: If credentials are invalid or provider is unavailable
        """
        if self.provider == 'gemini':
            return self._validate_gemini_credentials()
        elif self.provider == 'bedrock':
            return self._validate_bedrock_credentials()
        
        return False
    
    def _validate_gemini_credentials(self) -> bool:
        """Validate Gemini API credentials.
        
        Returns:
            True if credentials are valid
            
        Raises:
            LLMProviderError: If API key is missing
        """
        credentials = self.get_api_credentials()
        api_key = credentials.get('api_key')
        
        if not api_key:
            raise LLMProviderError("Gemini API key is required")
        
        # Basic validation - check if key is not empty and has reasonable length
        if len(api_key) < 10:
            raise LLMProviderError("Gemini API key appears to be invalid")
        
        return True
    
    def _validate_bedrock_credentials(self) -> bool:
        """Validate AWS Bedrock credentials and access.
        
        Returns:
            True if credentials are valid and Bedrock is accessible
            
        Raises:
            LLMProviderError: If credentials are invalid or Bedrock is unavailable
        """
        credentials = self.get_api_credentials()
        region = credentials.get('region')
        
        try:
            # Create Bedrock runtime client
            self._bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=region
            )
            
            # Verify we can access the service by listing foundation models
            # This validates both credentials and service availability
            bedrock_client = boto3.client('bedrock', region_name=region)
            bedrock_client.list_foundation_models(
                byProvider='anthropic'
            )
            
            return True
            
        except NoCredentialsError:
            raise LLMProviderError(
                "AWS credentials not found. Configure AWS credentials via "
                "environment variables, ~/.aws/credentials, or IAM role."
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            raise LLMProviderError(
                f"AWS Bedrock access failed ({error_code}): {error_message}"
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to validate Bedrock credentials: {str(e)}")
    
    def get_bedrock_client(self):
        """Get boto3 Bedrock runtime client.
        
        Returns:
            boto3 bedrock-runtime client
            
        Raises:
            LLMProviderError: If provider is not Bedrock or client not initialized
        """
        if self.provider != 'bedrock':
            raise LLMProviderError("Bedrock client only available for Bedrock provider")
        
        if not self._bedrock_client:
            credentials = self.get_api_credentials()
            self._bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=credentials.get('region')
            )
        
        return self._bedrock_client
