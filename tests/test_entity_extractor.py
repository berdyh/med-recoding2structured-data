"""Unit tests for ClinicalEntityExtractor.

Tests entity extraction methods, error handling, retry logic, and relationship grouping.
"""

import pytest
import yaml
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from entity_extractor import ClinicalEntityExtractor, ExtractionError
from llm_provider import LLMProviderManager


class TestClinicalEntityExtractor:
    """Test ClinicalEntityExtractor class."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        mock_provider = Mock(spec=LLMProviderManager)
        mock_provider.get_provider.return_value = 'gemini'
        mock_provider.validate_credentials.return_value = True
        mock_provider.get_api_credentials.return_value = {
            'api_key': 'test-key',
            'model': 'gemini-2.5-pro',
            'use_custom_endpoint': False
        }
        return mock_provider
    
    @pytest.fixture
    def few_shot_config_file(self):
        """Create a temporary few-shot examples config file."""
        config = {
            'symptoms': [
                {
                    'text': 'Patient has severe headache for 3 days.',
                    'extractions': [
                        {'class': 'symptom_name', 'text': 'headache', 'attributes': {'symptom_group': 'sym_1'}},
                        {'class': 'severity', 'text': 'severe', 'attributes': {'symptom_group': 'sym_1'}},
                        {'class': 'duration', 'text': '3 days', 'attributes': {'symptom_group': 'sym_1'}},
                    ]
                }
            ],
            'medications': [
                {
                    'text': 'Patient takes Aspirin 100mg daily.',
                    'extractions': [
                        {'class': 'medication', 'text': 'Aspirin', 'attributes': {'medication_group': 'med_1'}},
                        {'class': 'dosage', 'text': '100mg', 'attributes': {'medication_group': 'med_1'}},
                        {'class': 'frequency', 'text': 'daily', 'attributes': {'medication_group': 'med_1'}},
                    ]
                }
            ],
            'diagnoses': [
                {
                    'text': 'Diagnosis: Migraine, probable.',
                    'extractions': [
                        {'class': 'diagnosis', 'text': 'Migraine', 'attributes': {'diagnosis_group': 'diag_1'}},
                        {'class': 'certainty', 'text': 'probable', 'attributes': {'diagnosis_group': 'diag_1'}},
                    ]
                }
            ],
            'vital_signs': [],
            'physical_exam': [],
            'red_flags': [],
            'follow_up': []
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def mock_langextract_result(self):
        """Create a mock LangExtract result."""
        mock_result = Mock()
        mock_extraction1 = Mock()
        mock_extraction1.extraction_class = 'symptom_name'
        mock_extraction1.extraction_text = 'headache'
        mock_extraction1.attributes = {'symptom_group': 'sym_1'}
        
        mock_extraction2 = Mock()
        mock_extraction2.extraction_class = 'severity'
        mock_extraction2.extraction_text = 'severe'
        mock_extraction2.attributes = {'symptom_group': 'sym_1'}
        
        mock_result.extractions = [mock_extraction1, mock_extraction2]
        return mock_result
    
    def test_init_with_valid_config(self, mock_llm_provider, few_shot_config_file):
        """Test initialization with valid few-shot config."""
        with patch('entity_extractor.lx'):
            extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
            assert extractor.llm_provider == mock_llm_provider
            assert extractor.few_shot_examples is not None
            assert 'symptoms' in extractor.few_shot_examples
    
    def test_init_with_missing_config(self, mock_llm_provider):
        """Test initialization fails with missing config file."""
        with patch('entity_extractor.lx'):
            with pytest.raises(ExtractionError, match="Few-shot examples file not found"):
                ClinicalEntityExtractor(mock_llm_provider, 'nonexistent.yaml')
    
    def test_init_without_langextract(self, mock_llm_provider, few_shot_config_file):
        """Test initialization fails when langextract is not installed."""
        with patch('entity_extractor.lx', None):
            with pytest.raises(ExtractionError, match="langextract library not installed"):
                ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
    
    @patch('entity_extractor.lx')
    def test_extract_symptoms(self, mock_lx, mock_llm_provider, few_shot_config_file, mock_langextract_result):
        """Test symptom extraction."""
        mock_lx.extract.return_value = mock_langextract_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_symptoms("Patient has severe headache.")
        
        assert len(result) == 2
        assert result[0]['class'] == 'symptom_name'
        assert result[0]['text'] == 'headache'
        assert result[0]['attributes']['symptom_group'] == 'sym_1'
        assert result[1]['class'] == 'severity'
        assert result[1]['text'] == 'severe'
    
    @patch('entity_extractor.lx')
    def test_extract_medications(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test medication extraction."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'medication'
        mock_extraction.extraction_text = 'Aspirin'
        mock_extraction.attributes = {'medication_group': 'med_1'}
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_medications("Patient takes Aspirin 100mg daily.")
        
        assert len(result) == 1
        assert result[0]['class'] == 'medication'
        assert result[0]['text'] == 'Aspirin'
        assert result[0]['attributes']['medication_group'] == 'med_1'
    
    @patch('entity_extractor.lx')
    def test_extract_diagnoses(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test diagnosis extraction."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'diagnosis'
        mock_extraction.extraction_text = 'Migraine'
        mock_extraction.attributes = {'diagnosis_group': 'diag_1'}
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_diagnoses("Diagnosis: Migraine, probable.")
        
        assert len(result) == 1
        assert result[0]['class'] == 'diagnosis'
        assert result[0]['text'] == 'Migraine'
    
    @patch('entity_extractor.lx')
    def test_extract_vital_signs(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test vital signs extraction."""
        mock_result = Mock()
        mock_result.extractions = []
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_vital_signs("No vital signs recorded.")
        
        assert len(result) == 0
    
    @patch('entity_extractor.lx')
    def test_extract_physical_exam(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test physical examination extraction."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'examination_type'
        mock_extraction.extraction_text = 'chest examination'
        mock_extraction.attributes = {}
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_physical_exam("Chest examination normal.")
        
        assert len(result) == 1
        assert result[0]['class'] == 'examination_type'
    
    @patch('entity_extractor.lx')
    def test_extract_red_flags(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test red flags extraction."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'warning_description'
        mock_extraction.extraction_text = 'severe chest pain'
        mock_extraction.attributes = {'warning_group': 'warn_1'}
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_red_flags("Red flag: severe chest pain.")
        
        assert len(result) == 1
        assert result[0]['class'] == 'warning_description'
        assert result[0]['attributes']['warning_group'] == 'warn_1'
    
    @patch('entity_extractor.lx')
    def test_extract_follow_up(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test follow-up plan extraction."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'follow_up_type'
        mock_extraction.extraction_text = 'follow-up appointment'
        mock_extraction.attributes = {'followup_group': 'fu_1'}
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_follow_up("Follow-up in 2 weeks.")
        
        assert len(result) == 1
        assert result[0]['class'] == 'follow_up_type'
        assert result[0]['attributes']['followup_group'] == 'fu_1'
    
    @patch('entity_extractor.lx')
    def test_extract_all(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test extract_all method orchestrates all extractions."""
        mock_result = Mock()
        mock_result.extractions = []
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_all("Sample consultation text.")
        
        assert isinstance(result, dict)
        assert 'symptoms' in result
        assert 'medications' in result
        assert 'diagnoses' in result
        assert 'vital_signs' in result
        assert 'physical_exam' in result
        assert 'red_flags' in result
        assert 'follow_up' in result
    
    @patch('entity_extractor.lx')
    @patch('entity_extractor.time.sleep')
    def test_retry_logic_on_failure(self, mock_sleep, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test retry logic when extraction fails."""
        # First call fails, second succeeds
        mock_result = Mock()
        mock_result.extractions = []
        
        mock_lx.extract.side_effect = [
            Exception("API rate limit exceeded"),
            mock_result
        ]
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        extractor.retry_attempts = 1
        
        result = extractor.extract_symptoms("Patient has headache.")
        
        # Should have retried once
        assert mock_lx.extract.call_count == 2
        assert mock_sleep.called
    
    @patch('entity_extractor.lx')
    def test_retry_exhausted_raises_error(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test that ExtractionError is raised when retries are exhausted."""
        mock_lx.extract.side_effect = Exception("API error")
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        extractor.retry_attempts = 1
        
        with pytest.raises(ExtractionError, match="Failed to extract symptoms"):
            extractor.extract_symptoms("Patient has headache.")
    
    @patch('entity_extractor.lx')
    def test_relationship_attribute_grouping(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test that relationship attributes (e.g., symptom_group) are preserved."""
        mock_result = Mock()
        
        # Create multiple extractions with same symptom_group
        mock_extraction1 = Mock()
        mock_extraction1.extraction_class = 'symptom_name'
        mock_extraction1.extraction_text = 'headache'
        mock_extraction1.attributes = {'symptom_group': 'sym_1'}
        
        mock_extraction2 = Mock()
        mock_extraction2.extraction_class = 'severity'
        mock_extraction2.extraction_text = 'severe'
        mock_extraction2.attributes = {'symptom_group': 'sym_1'}
        
        mock_extraction3 = Mock()
        mock_extraction3.extraction_class = 'duration'
        mock_extraction3.extraction_text = '3 days'
        mock_extraction3.attributes = {'symptom_group': 'sym_1'}
        
        mock_result.extractions = [mock_extraction1, mock_extraction2, mock_extraction3]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_symptoms("Patient has severe headache for 3 days.")
        
        # All should have same symptom_group
        assert len(result) == 3
        assert all(entity['attributes'].get('symptom_group') == 'sym_1' for entity in result)
    
    @patch('entity_extractor.lx')
    def test_medication_group_attribute(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test medication_group attribute for grouping related medication details."""
        mock_result = Mock()
        
        mock_extraction1 = Mock()
        mock_extraction1.extraction_class = 'medication'
        mock_extraction1.extraction_text = 'Aspirin'
        mock_extraction1.attributes = {'medication_group': 'med_1'}
        
        mock_extraction2 = Mock()
        mock_extraction2.extraction_class = 'dosage'
        mock_extraction2.extraction_text = '100mg'
        mock_extraction2.attributes = {'medication_group': 'med_1'}
        
        mock_extraction3 = Mock()
        mock_extraction3.extraction_class = 'frequency'
        mock_extraction3.extraction_text = 'daily'
        mock_extraction3.attributes = {'medication_group': 'med_1'}
        
        mock_result.extractions = [mock_extraction1, mock_extraction2, mock_extraction3]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_medications("Patient takes Aspirin 100mg daily.")
        
        # All should have same medication_group
        assert len(result) == 3
        assert all(entity['attributes'].get('medication_group') == 'med_1' for entity in result)
    
    @patch('entity_extractor.lx')
    def test_diagnosis_group_attribute(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test diagnosis_group attribute for grouping related diagnosis details."""
        mock_result = Mock()
        
        mock_extraction1 = Mock()
        mock_extraction1.extraction_class = 'diagnosis'
        mock_extraction1.extraction_text = 'Migraine'
        mock_extraction1.attributes = {'diagnosis_group': 'diag_1'}
        
        mock_extraction2 = Mock()
        mock_extraction2.extraction_class = 'certainty'
        mock_extraction2.extraction_text = 'probable'
        mock_extraction2.attributes = {'diagnosis_group': 'diag_1'}
        
        mock_result.extractions = [mock_extraction1, mock_extraction2]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_diagnoses("Diagnosis: Migraine, probable.")
        
        # Both should have same diagnosis_group
        assert len(result) == 2
        assert all(entity['attributes'].get('diagnosis_group') == 'diag_1' for entity in result)
    
    @patch('entity_extractor.lx')
    def test_empty_extraction_result(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test handling of empty extraction results."""
        mock_result = Mock()
        mock_result.extractions = []
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_symptoms("No symptoms mentioned.")
        
        assert len(result) == 0
        assert isinstance(result, list)
    
    @patch('entity_extractor.lx')
    def test_bedrock_provider_support(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test Bedrock provider support."""
        mock_llm_provider.get_provider.return_value = 'bedrock'
        mock_llm_provider.get_api_credentials.return_value = {
            'model_id': 'anthropic.claude-sonnet-4-5-20250929-v1:0',
            'use_custom_endpoint': False
        }
        mock_bedrock_client = Mock()
        mock_llm_provider.get_bedrock_client.return_value = mock_bedrock_client
        
        mock_result = Mock()
        mock_result.extractions = []
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_symptoms("Patient has headache.")
        
        # Verify bedrock_client was passed to lx.extract
        mock_lx.extract.assert_called_once()
        call_kwargs = mock_lx.extract.call_args[1]
        assert 'bedrock_client' in call_kwargs
        assert call_kwargs['bedrock_client'] == mock_bedrock_client
    
    @patch('entity_extractor.lx')
    def test_parse_extraction_result_with_attributes(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test parsing extraction result with attributes."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'symptom_name'
        mock_extraction.extraction_text = 'headache'
        mock_extraction.attributes = {'symptom_group': 'sym_1', 'severity': 'moderate'}
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_symptoms("Patient has headache.")
        
        assert len(result) == 1
        assert result[0]['attributes'] == {'symptom_group': 'sym_1', 'severity': 'moderate'}
    
    @patch('entity_extractor.lx')
    def test_parse_extraction_result_without_attributes(self, mock_lx, mock_llm_provider, few_shot_config_file):
        """Test parsing extraction result without attributes."""
        mock_result = Mock()
        mock_extraction = Mock()
        mock_extraction.extraction_class = 'symptom_name'
        mock_extraction.extraction_text = 'headache'
        # No attributes property
        del mock_extraction.attributes
        mock_result.extractions = [mock_extraction]
        mock_lx.extract.return_value = mock_result
        
        extractor = ClinicalEntityExtractor(mock_llm_provider, few_shot_config_file)
        result = extractor.extract_symptoms("Patient has headache.")
        
        assert len(result) == 1
        assert result[0]['attributes'] == {}  # Should default to empty dict

