"""Unit tests for LLM provider management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError

import sys
sys.path.insert(0, 'src')

from llm_provider import LLMProviderManager, LLMProviderError


class TestLLMProviderManager:
    """Test cases for LLMProviderManager class."""
    
    def test_init_with_gemini_provider(self):
        """Test initialization with Gemini provider."""
        config = {
            'provider': 'gemini',
            'gemini': {
                'api_key': 'test-api-key',
                'model': 'gemini-2.5-pro'
            }
        }
        
        manager = LLMProviderManager(config)
        assert manager.get_provider() == 'gemini'
    
    def test_init_with_bedrock_provider(self):
        """Test initialization with Bedrock provider."""
        config = {
            'provider': 'bedrock',
            'bedrock': {
                'region': 'us-east-1',
                'model_id': 'anthropic.claude-sonnet-4-5-20250929-v1:0'
            }
        }
        
        manager = LLMProviderManager(config)
        assert manager.get_provider() == 'bedrock'
    
    def test_init_with_invalid_provider(self):
        """Test initialization with invalid provider raises error."""
        config = {'provider': 'invalid-provider'}
        
        with pytest.raises(LLMProviderError) as exc_info:
            LLMProviderManager(config)
        
        assert 'Unsupported provider' in str(exc_info.value)
    
    def test_get_gemini_credentials(self):
        """Test getting Gemini credentials."""
        config = {
            'provider': 'gemini',
            'gemini': {
                'api_key': 'test-api-key-12345',
                'model': 'gemini-2.5-pro'
            }
        }
        
        manager = LLMProviderManager(config)
        credentials = manager.get_api_credentials()
        
        assert credentials['api_key'] == 'test-api-key-12345'
        assert credentials['model'] == 'gemini-2.5-pro'
    
    def test_get_gemini_credentials_missing_api_key(self):
        """Test getting Gemini credentials without API key raises error."""
        config = {
            'provider': 'gemini',
            'gemini': {}
        }
        
        manager = LLMProviderManager(config)
        
        with pytest.raises(LLMProviderError) as exc_info:
            manager.get_api_credentials()
        
        assert 'API key not configured' in str(exc_info.value)
    
    def test_get_bedrock_credentials(self):
        """Test getting Bedrock credentials."""
        config = {
            'provider': 'bedrock',
            'bedrock': {
                'region': 'us-west-2',
                'model_id': 'anthropic.claude-sonnet-4-5-20250929-v1:0'
            }
        }
        
        manager = LLMProviderManager(config)
        credentials = manager.get_api_credentials()
        
        assert credentials['region'] == 'us-west-2'
        assert credentials['model_id'] == 'anthropic.claude-sonnet-4-5-20250929-v1:0'
    
    def test_get_bedrock_credentials_with_defaults(self):
        """Test getting Bedrock credentials uses defaults when not specified."""
        config = {
            'provider': 'bedrock',
            'bedrock': {}
        }
        
        manager = LLMProviderManager(config)
        credentials = manager.get_api_credentials()
        
        assert credentials['region'] == 'us-east-1'
        assert 'anthropic.claude-sonnet' in credentials['model_id']
    
    def test_validate_gemini_credentials_success(self):
        """Test successful Gemini credential validation."""
        config = {
            'provider': 'gemini',
            'gemini': {
                'api_key': 'valid-api-key-12345',
                'model': 'gemini-2.5-pro'
            }
        }
        
        manager = LLMProviderManager(config)
        assert manager.validate_credentials() is True
    
    def test_validate_gemini_credentials_missing_key(self):
        """Test Gemini validation fails with missing API key."""
        config = {
            'provider': 'gemini',
            'gemini': {}
        }
        
        manager = LLMProviderManager(config)
        
        with pytest.raises(LLMProviderError):
            manager.validate_credentials()
    
    def test_validate_gemini_credentials_invalid_key(self):
        """Test Gemini validation fails with invalid API key."""
        config = {
            'provider': 'gemini',
            'gemini': {
                'api_key': 'short'
            }
        }
        
        manager = LLMProviderManager(config)
        
        with pytest.raises(LLMProviderError) as exc_info:
            manager.validate_credentials()
        
        assert 'invalid' in str(exc_info.value).lower()
    
    @patch('llm_provider.boto3.client')
    def test_validate_bedrock_credentials_success(self, mock_boto_client):
        """Test successful Bedrock credential validation."""
        # Mock both bedrock-runtime and bedrock clients
        mock_runtime_client = MagicMock()
        mock_bedrock_client = MagicMock()
        mock_bedrock_client.list_foundation_models.return_value = {'modelSummaries': []}
        
        def client_factory(service_name, **kwargs):
            if service_name == 'bedrock-runtime':
                return mock_runtime_client
            elif service_name == 'bedrock':
                return mock_bedrock_client
            return MagicMock()
        
        mock_boto_client.side_effect = client_factory
        
        config = {
            'provider': 'bedrock',
            'bedrock': {
                'region': 'us-east-1',
                'model_id': 'anthropic.claude-sonnet-4-5-20250929-v1:0'
            }
        }
        
        manager = LLMProviderManager(config)
        assert manager.validate_credentials() is True
    
    @patch('llm_provider.boto3.client')
    def test_validate_bedrock_credentials_no_credentials(self, mock_boto_client):
        """Test Bedrock validation fails with no AWS credentials."""
        mock_boto_client.side_effect = NoCredentialsError()
        
        config = {
            'provider': 'bedrock',
            'bedrock': {
                'region': 'us-east-1'
            }
        }
        
        manager = LLMProviderManager(config)
        
        with pytest.raises(LLMProviderError) as exc_info:
            manager.validate_credentials()
        
        assert 'credentials not found' in str(exc_info.value).lower()
    
    @patch('llm_provider.boto3.client')
    def test_validate_bedrock_credentials_access_denied(self, mock_boto_client):
        """Test Bedrock validation fails with access denied."""
        mock_client = MagicMock()
        mock_client.list_foundation_models.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
            'ListFoundationModels'
        )
        mock_boto_client.return_value = mock_client
        
        config = {
            'provider': 'bedrock',
            'bedrock': {
                'region': 'us-east-1'
            }
        }
        
        manager = LLMProviderManager(config)
        
        with pytest.raises(LLMProviderError) as exc_info:
            manager.validate_credentials()
        
        assert 'AccessDeniedException' in str(exc_info.value)
    
    @patch('llm_provider.boto3.client')
    def test_get_bedrock_client(self, mock_boto_client):
        """Test getting Bedrock client."""
        mock_runtime_client = MagicMock()
        mock_boto_client.return_value = mock_runtime_client
        
        config = {
            'provider': 'bedrock',
            'bedrock': {
                'region': 'us-east-1'
            }
        }
        
        manager = LLMProviderManager(config)
        client = manager.get_bedrock_client()
        
        assert client == mock_runtime_client
        mock_boto_client.assert_called_with('bedrock-runtime', region_name='us-east-1')
    
    def test_get_bedrock_client_wrong_provider(self):
        """Test getting Bedrock client with non-Bedrock provider raises error."""
        config = {
            'provider': 'gemini',
            'gemini': {
                'api_key': 'test-key-12345'
            }
        }
        
        manager = LLMProviderManager(config)
        
        with pytest.raises(LLMProviderError) as exc_info:
            manager.get_bedrock_client()
        
        assert 'only available for Bedrock' in str(exc_info.value)
