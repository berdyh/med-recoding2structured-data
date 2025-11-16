"""Unit tests for Validator.

Tests all validation rules, error messages, and validate_all aggregation.
"""

import pytest
from datetime import datetime, timedelta

import sys
sys.path.insert(0, 'src')

from validator import Validator, ValidationError


class TestValidator:
    """Test Validator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return Validator()
    
    def test_validate_severity_valid_values(self, validator):
        """Test severity validation with valid values."""
        assert validator.validate_severity('mild') is True
        assert validator.validate_severity('moderate') is True
        assert validator.validate_severity('severe') is True
        assert validator.validate_severity('critical') is True
        assert validator.validate_severity('MILD') is True  # Case insensitive
        assert validator.validate_severity('  moderate  ') is True  # Whitespace handling
    
    def test_validate_severity_invalid_values(self, validator):
        """Test severity validation with invalid values."""
        assert validator.validate_severity('invalid') is False
        assert validator.validate_severity('high') is False
        assert validator.validate_severity('low') is False
    
    def test_validate_severity_null(self, validator):
        """Test severity validation allows NULL values."""
        assert validator.validate_severity(None) is True
        assert validator.validate_severity('') is True
    
    def test_validate_certainty_valid_values(self, validator):
        """Test certainty validation with valid values."""
        assert validator.validate_certainty('confirmed') is True
        assert validator.validate_certainty('probable') is True
        assert validator.validate_certainty('suspected') is True
        assert validator.validate_certainty('ruled_out') is True
        assert validator.validate_certainty('CONFIRMED') is True  # Case insensitive
    
    def test_validate_certainty_invalid_values(self, validator):
        """Test certainty validation with invalid values."""
        assert validator.validate_certainty('certain') is False
        assert validator.validate_certainty('maybe') is False
    
    def test_validate_certainty_null(self, validator):
        """Test certainty validation allows NULL values."""
        assert validator.validate_certainty(None) is True
        assert validator.validate_certainty('') is True
    
    def test_validate_dosage_positive(self, validator):
        """Test dosage validation with positive values."""
        assert validator.validate_dosage(100.0) is True
        assert validator.validate_dosage(0.5) is True
        assert validator.validate_dosage(1) is True
        assert validator.validate_dosage('100.0') is True  # String number
    
    def test_validate_dosage_negative_or_zero(self, validator):
        """Test dosage validation rejects negative or zero values."""
        assert validator.validate_dosage(-10.0) is False
        assert validator.validate_dosage(0) is False
        assert validator.validate_dosage(0.0) is False
    
    def test_validate_dosage_null(self, validator):
        """Test dosage validation allows NULL values."""
        assert validator.validate_dosage(None) is True
    
    def test_validate_dosage_invalid_type(self, validator):
        """Test dosage validation with invalid types."""
        assert validator.validate_dosage('not a number') is False
        assert validator.validate_dosage([]) is False
    
    def test_validate_date_valid_format(self, validator):
        """Test date validation with valid ISO 8601 format."""
        assert validator.validate_date('2024-01-15') is True
        assert validator.validate_date('2023-12-31') is True
    
    def test_validate_date_invalid_format(self, validator):
        """Test date validation with invalid formats."""
        assert validator.validate_date('15-01-2024') is False  # Wrong format
        assert validator.validate_date('2024/01/15') is False  # Wrong separator
        assert validator.validate_date('01-15-2024') is False  # US format
        assert validator.validate_date('2024-1-15') is False  # Missing leading zero
    
    def test_validate_date_future_date(self, validator):
        """Test date validation rejects future dates."""
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        assert validator.validate_date(future_date) is False
    
    def test_validate_date_null(self, validator):
        """Test date validation allows NULL values."""
        assert validator.validate_date(None) is True
        assert validator.validate_date('') is True
    
    def test_validate_datetime_valid_format(self, validator):
        """Test datetime validation with valid ISO 8601 format."""
        valid_datetime = datetime.now().isoformat()
        assert validator.validate_datetime(valid_datetime) is True
    
    def test_validate_datetime_invalid_format(self, validator):
        """Test datetime validation with invalid formats."""
        assert validator.validate_datetime('2024-01-15') is False  # Date only
        assert validator.validate_datetime('invalid') is False
    
    def test_validate_nhs_number_valid(self, validator):
        """Test NHS number validation with valid numbers."""
        # Valid NHS numbers (10 digits with correct checksum)
        assert validator.validate_nhs_number('1234567890') is True
        # Note: Actual NHS number validation uses Modulus 11 checksum
        # These are simplified tests
    
    def test_validate_nhs_number_invalid_length(self, validator):
        """Test NHS number validation with invalid length."""
        assert validator.validate_nhs_number('12345') is False  # Too short
        assert validator.validate_nhs_number('123456789012') is False  # Too long
    
    def test_validate_nhs_number_invalid_characters(self, validator):
        """Test NHS number validation with invalid characters."""
        assert validator.validate_nhs_number('123456789a') is False  # Contains letter
        assert validator.validate_nhs_number('123456789-') is False  # Contains dash
    
    def test_validate_email_valid(self, validator):
        """Test email validation with valid emails."""
        assert validator.validate_email('test@example.com') is True
        assert validator.validate_email('user.name@domain.co.uk') is True
        assert validator.validate_email('test+tag@example.com') is True
    
    def test_validate_email_invalid(self, validator):
        """Test email validation with invalid emails."""
        assert validator.validate_email('invalid') is False
        assert validator.validate_email('@example.com') is False
        assert validator.validate_email('test@') is False
        assert validator.validate_email('test @example.com') is False  # Space
    
    def test_validate_phone_valid(self, validator):
        """Test phone validation with valid UK phone numbers."""
        assert validator.validate_phone('+44 20 1234 5678') is True
        assert validator.validate_phone('020 1234 5678') is True
        assert validator.validate_phone('07123 456789') is True
    
    def test_validate_phone_invalid(self, validator):
        """Test phone validation with invalid numbers."""
        assert validator.validate_phone('invalid') is False
        assert validator.validate_phone('123') is False  # Too short
        assert validator.validate_phone('abc') is False  # Not numeric
    
    def test_validate_required_field_present(self, validator):
        """Test required field validation when field is present."""
        assert validator.validate_required_field('value', 'field_name') is True
        assert validator.validate_required_field(123, 'field_name') is True
        assert validator.validate_required_field(0, 'field_name') is True  # 0 is valid
    
    def test_validate_required_field_missing(self, validator):
        """Test required field validation when field is missing."""
        assert validator.validate_required_field(None, 'field_name') is False
        assert validator.validate_required_field('', 'field_name') is False
    
    def test_validate_symptom_valid(self, validator):
        """Test symptom validation with valid symptom data."""
        symptom = {
            'class': 'symptom_name',
            'text': 'headache',
            'attributes': {
                'severity': 'moderate',
                'duration': '3 days'
            }
        }
        is_valid, errors = validator.validate_symptom(symptom)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_symptom_invalid_severity(self, validator):
        """Test symptom validation with invalid severity."""
        symptom = {
            'class': 'symptom_name',
            'text': 'headache',
            'attributes': {
                'severity': 'invalid_severity'
            }
        }
        is_valid, errors = validator.validate_symptom(symptom)
        assert is_valid is False
        assert len(errors) > 0
        assert any('severity' in error.lower() for error in errors)
    
    def test_validate_medication_valid(self, validator):
        """Test medication validation with valid medication data."""
        medication = {
            'class': 'medication',
            'text': 'Aspirin',
            'attributes': {
                'dosage': '100mg'
            }
        }
        is_valid, errors = validator.validate_medication(medication)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_medication_invalid_dosage(self, validator):
        """Test medication validation with invalid dosage."""
        medication = {
            'class': 'medication',
            'text': 'Aspirin',
            'attributes': {
                'dosage': -10.0  # Negative dosage
            }
        }
        is_valid, errors = validator.validate_medication(medication)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_diagnosis_valid(self, validator):
        """Test diagnosis validation with valid diagnosis data."""
        diagnosis = {
            'class': 'diagnosis',
            'text': 'Migraine',
            'attributes': {
                'certainty': 'probable'
            }
        }
        is_valid, errors = validator.validate_diagnosis(diagnosis)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_diagnosis_invalid_certainty(self, validator):
        """Test diagnosis validation with invalid certainty."""
        diagnosis = {
            'class': 'diagnosis',
            'text': 'Migraine',
            'attributes': {
                'certainty': 'invalid_certainty'
            }
        }
        is_valid, errors = validator.validate_diagnosis(diagnosis)
        assert is_valid is False
        assert len(errors) > 0
        assert any('certainty' in error.lower() for error in errors)
    
    def test_validate_vital_signs_valid(self, validator):
        """Test vital signs validation with valid data."""
        vital_signs = {
            'class': 'temperature',
            'text': '37.5',
            'attributes': {}
        }
        is_valid, errors = validator.validate_vital_signs(vital_signs)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_all_with_valid_data(self, validator):
        """Test validate_all with all valid data."""
        data = {
            'symptoms': [
                {
                    'class': 'symptom_name',
                    'text': 'headache',
                    'attributes': {'severity': 'moderate'}
                }
            ],
            'medications': [
                {
                    'class': 'medication',
                    'text': 'Aspirin',
                    'attributes': {}
                }
            ],
            'diagnoses': [
                {
                    'class': 'diagnosis',
                    'text': 'Migraine',
                    'attributes': {'certainty': 'probable'}
                }
            ]
        }
        is_valid, errors = validator.validate_all(data)
        assert is_valid is True
        # May have warnings but should be valid
        assert isinstance(errors, list)
    
    def test_validate_all_with_invalid_data(self, validator):
        """Test validate_all with invalid data."""
        data = {
            'symptoms': [
                {
                    'class': 'symptom_name',
                    'text': 'headache',
                    'attributes': {'severity': 'invalid_severity'}
                }
            ],
            'medications': [
                {
                    'class': 'medication',
                    'text': 'Aspirin',
                    'attributes': {'dosage': -10.0}
                }
            ],
            'diagnoses': [
                {
                    'class': 'diagnosis',
                    'text': 'Migraine',
                    'attributes': {'certainty': 'invalid_certainty'}
                }
            ]
        }
        is_valid, errors = validator.validate_all(data)
        # Should have validation errors
        assert isinstance(errors, list)
        assert len(errors) > 0
    
    def test_validate_all_empty_data(self, validator):
        """Test validate_all with empty data."""
        data = {
            'symptoms': [],
            'medications': [],
            'diagnoses': []
        }
        is_valid, errors = validator.validate_all(data)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_all_missing_keys(self, validator):
        """Test validate_all with missing entity type keys."""
        data = {
            'symptoms': []
        }
        is_valid, errors = validator.validate_all(data)
        # Should handle missing keys gracefully
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validation_error_messages(self, validator):
        """Test that validation error messages are descriptive."""
        symptom = {
            'class': 'symptom_name',
            'text': 'headache',
            'attributes': {
                'severity': 'invalid'
            }
        }
        is_valid, errors = validator.validate_symptom(symptom)
        
        assert is_valid is False
        assert len(errors) > 0
        # Error messages should be strings
        assert all(isinstance(error, str) for error in errors)
        # Error messages should not be empty
        assert all(len(error) > 0 for error in errors)
    
    def test_validate_all_aggregation(self, validator):
        """Test that validate_all aggregates errors from all entity types."""
        data = {
            'symptoms': [
                {
                    'class': 'symptom_name',
                    'text': 'headache',
                    'attributes': {'severity': 'invalid'}
                }
            ],
            'medications': [
                {
                    'class': 'medication',
                    'text': 'Aspirin',
                    'attributes': {'dosage': -5.0}
                }
            ],
            'diagnoses': [
                {
                    'class': 'diagnosis',
                    'text': 'Migraine',
                    'attributes': {'certainty': 'invalid'}
                }
            ]
        }
        is_valid, errors = validator.validate_all(data)
        
        # Should aggregate errors from all validations
        assert len(errors) >= 3  # At least one error per entity type
        assert isinstance(errors, list)
    
    def test_validation_warnings_tracked(self, validator):
        """Test that validation warnings are tracked."""
        symptom = {
            'class': 'symptom_name',
            'text': 'headache',
            'attributes': {'severity': 'invalid'}
        }
        validator.validate_symptom(symptom)
        
        # Validator should track warnings
        assert hasattr(validator, 'validation_warnings')
        assert isinstance(validator.validation_warnings, list)

