"""LLM provider management for GP Consultation Extractor.

This module manages connections to different LLM providers (Gemini and AWS Bedrock)
and provides a unified interface for credential validation and provider selection.
"""

import os
import boto3
import requests
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
            bedrock_config = self.config.get('bedrock', {})
            region = bedrock_config.get('region', 'us-east-1')
            model_id = bedrock_config.get(
                'model_id',
                'anthropic.claude-sonnet-4-5-20250929-v1:0'
            )
            
            credentials = {
                'region': region,
                'model_id': model_id
            }
            
            # Check if using custom API Gateway endpoint
            if bedrock_config.get('use_custom_endpoint') or bedrock_config.get('api_endpoint'):
                credentials['use_custom_endpoint'] = True
                credentials['api_endpoint'] = bedrock_config.get('api_endpoint')
                credentials['api_key'] = bedrock_config.get('api_key')
                
                if not credentials['api_endpoint']:
                    raise LLMProviderError(
                        "Bedrock API endpoint not configured. "
                        "Set BEDROCK_API_ENDPOINT environment variable."
                    )
                if not credentials['api_key']:
                    raise LLMProviderError(
                        "Bedrock API key not configured. "
                        "Set BEDROCK_API_KEY environment variable."
                    )
            else:
                # Standard boto3 credentials
                credentials['use_custom_endpoint'] = False
                
                # Add explicit AWS credentials if provided
                if 'aws_access_key_id' in bedrock_config:
                    credentials['aws_access_key_id'] = bedrock_config['aws_access_key_id']
                if 'aws_secret_access_key' in bedrock_config:
                    credentials['aws_secret_access_key'] = bedrock_config['aws_secret_access_key']
            
            return credentials
        
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
        
        # Check if using custom API Gateway endpoint
        if credentials.get('use_custom_endpoint'):
            # Validate custom endpoint configuration
            api_endpoint = credentials.get('api_endpoint')
            api_key = credentials.get('api_key')
            
            if not api_endpoint or not api_key:
                raise LLMProviderError(
                    "Custom Bedrock endpoint requires both BEDROCK_API_ENDPOINT and BEDROCK_API_KEY"
                )
            
            # Test the endpoint with a simple health check or minimal request
            try:
                # We can't really validate without making a real API call
                # Just check the endpoint is a valid URL
                if not api_endpoint.startswith('http'):
                    raise LLMProviderError(f"Invalid API endpoint URL: {api_endpoint}")
                
                return True
            except Exception as e:
                raise LLMProviderError(f"Failed to validate custom Bedrock endpoint: {e}")
        
        else:
            # Standard boto3 validation
            region = credentials.get('region')
            
            # Prepare boto3 client kwargs
            client_kwargs = {'region_name': region}
            
            # Add explicit credentials if provided
            if 'aws_access_key_id' in credentials and 'aws_secret_access_key' in credentials:
                client_kwargs['aws_access_key_id'] = credentials['aws_access_key_id']
                client_kwargs['aws_secret_access_key'] = credentials['aws_secret_access_key']
            
            try:
                # Create Bedrock runtime client
                self._bedrock_client = boto3.client('bedrock-runtime', **client_kwargs)
                
                # Verify we can access the service by listing foundation models
                # This validates both credentials and service availability
                bedrock_client = boto3.client('bedrock', **client_kwargs)
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
        
        credentials = self.get_api_credentials()
        
        # Check if using custom endpoint
        if credentials.get('use_custom_endpoint'):
            raise LLMProviderError(
                "Custom endpoint configured. Use invoke_custom_endpoint() instead of get_bedrock_client()"
            )
        
        if not self._bedrock_client:
            # Prepare boto3 client kwargs
            client_kwargs = {'region_name': credentials.get('region')}
            
            # Add explicit credentials if provided
            if 'aws_access_key_id' in credentials and 'aws_secret_access_key' in credentials:
                client_kwargs['aws_access_key_id'] = credentials['aws_access_key_id']
                client_kwargs['aws_secret_access_key'] = credentials['aws_secret_access_key']
            
            self._bedrock_client = boto3.client('bedrock-runtime', **client_kwargs)
        
        return self._bedrock_client
    
    def invoke_custom_endpoint(self, payload: Dict) -> Dict:
        """Invoke custom Bedrock API Gateway endpoint.
        
        Args:
            payload: JSON payload to send to the endpoint
            
        Returns:
            Response JSON from the endpoint
            
        Raises:
            LLMProviderError: If request fails
        """
        if self.provider != 'bedrock':
            raise LLMProviderError("Custom endpoint only available for Bedrock provider")
        
        credentials = self.get_api_credentials()
        
        if not credentials.get('use_custom_endpoint'):
            raise LLMProviderError("Custom endpoint not configured")
        
        api_endpoint = credentials['api_endpoint']
        api_key = credentials['api_key']
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key
        }
        
        try:
            response = requests.post(
                api_endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise LLMProviderError(f"Custom endpoint request failed: {e}")
