"""Data validation for extracted clinical entities.

This module validates extracted data against business rules and database constraints.
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails critically."""
    pass


class Validator:
    """Validates extracted clinical data against business rules."""
    
    # Valid values for constrained fields
    VALID_SEVERITIES = ['mild', 'moderate', 'severe', 'critical']
    VALID_CERTAINTIES = ['confirmed', 'probable', 'suspected', 'ruled_out']
    VALID_GENDERS = ['M', 'F', 'Other', 'Unknown']
    
    def __init__(self):
        """Initialize validator."""
        self.validation_warnings = []
    
    def validate_severity(self, severity: str) -> bool:
        """Validate severity is in allowed values.
        
        Args:
            severity: Severity value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not severity:
            return True  # NULL is allowed
        
        severity_lower = severity.lower().strip()
        return severity_lower in self.VALID_SEVERITIES
    
    def validate_certainty(self, certainty: str) -> bool:
        """Validate diagnostic certainty.
        
        Args:
            certainty: Certainty value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not certainty:
            return True  # NULL is allowed
        
        certainty_lower = certainty.lower().strip()
        return certainty_lower in self.VALID_CERTAINTIES
    
    def validate_dosage(self, dosage: float) -> bool:
        """Validate dosage is positive.
        
        Args:
            dosage: Dosage value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if dosage is None:
            return True  # NULL is allowed
        
        try:
            dosage_float = float(dosage)
            return dosage_float > 0
        except (ValueError, TypeError):
            return False
    
    def validate_date(self, date_str: str) -> bool:
        """Validate date format and logical consistency.
        
        Args:
            date_str: Date string to validate (ISO 8601 format)
            
        Returns:
            True if valid, False otherwise
        """
        if not date_str:
            return True  # NULL is allowed
        
        # Check ISO 8601 format (YYYY-MM-DD)
        iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(iso_pattern, date_str):
            return False
        
        try:
            date = datetime.fromisoformat(date_str)
            
            # Date should not be in the future
            if date > datetime.now():
                return False
            
            # Date should not be too far in the past (e.g., before 1900)
            if date.year < 1900:
                return False
            
            return True
        except ValueError:
            return False
    
    def validate_datetime(self, datetime_str: str) -> bool:
        """Validate datetime format and logical consistency.
        
        Args:
            datetime_str: Datetime string to validate (ISO 8601 format)
            
        Returns:
            True if valid, False otherwise
        """
        if not datetime_str:
            return True  # NULL is allowed
        
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
            # Datetime should not be in the future
            if dt > datetime.now():
                return False
            
            return True
        except ValueError:
            return False
    
    def validate_nhs_number(self, nhs_number: str) -> bool:
        """Validate NHS number format and checksum.
        
        Args:
            nhs_number: NHS number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not nhs_number:
            return True  # NULL is allowed
        
        # NHS number must be 10 digits
        if not re.match(r'^\d{10}$', nhs_number):
            return False
        
        # Validate checksum using Modulus 11 algorithm
        digits = [int(d) for d in nhs_number]
        weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        
        total = sum(d * w for d, w in zip(digits[:9], weights))
        remainder = total % 11
        checksum = 11 - remainder
        
        if checksum == 11:
            checksum = 0
        
        # Checksum of 10 is invalid
        if checksum == 10:
            return False
        
        return digits[9] == checksum
    
    def validate_email(self, email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return True  # NULL is allowed
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate UK phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return True  # NULL is allowed
        
        # UK phone number patterns
        uk_patterns = [
            r'^\+44\s?\d{4}\s?\d{6}$',  # +44 XXXX XXXXXX
            r'^0\d{10}$',  # 0XXXXXXXXXX
            r'^0\d{4}\s?\d{6}$',  # 0XXXX XXXXXX
        ]
        
        return any(re.match(pattern, phone) for pattern in uk_patterns)
    
    def validate_required_field(self, value: Any, field_name: str) -> bool:
        """Validate that a required field is not NULL or empty.
        
        Args:
            value: Field value to validate
            field_name: Name of the field (for logging)
            
        Returns:
            True if valid, False otherwise
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            self.validation_warnings.append(f"Required field '{field_name}' is empty")
            return False
        return True
    
    def validate_symptom(self, symptom: Dict) -> Tuple[bool, List[str]]:
        """Validate a symptom entity.
        
        Args:
            symptom: Symptom dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate severity
        if 'severity' in symptom and symptom['severity']:
            if not self.validate_severity(symptom['severity']):
                errors.append(f"Invalid severity: {symptom['severity']}")
        
        # Validate duration (should be positive if present)
        if 'duration_days' in symptom and symptom['duration_days'] is not None:
            try:
                duration = int(symptom['duration_days'])
                if duration < 0:
                    errors.append(f"Duration cannot be negative: {duration}")
            except (ValueError, TypeError):
                errors.append(f"Invalid duration format: {symptom.get('duration_days')}")
        
        # Validate onset date
        if 'onset_date' in symptom and symptom['onset_date']:
            if not self.validate_date(symptom['onset_date']):
                errors.append(f"Invalid onset date: {symptom['onset_date']}")
        
        return len(errors) == 0, errors
    
    def validate_medication(self, medication: Dict) -> Tuple[bool, List[str]]:
        """Validate a medication entity.
        
        Args:
            medication: Medication dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate dosage
        if 'dosage_value' in medication and medication['dosage_value'] is not None:
            if not self.validate_dosage(medication['dosage_value']):
                errors.append(f"Invalid dosage: {medication['dosage_value']}")
        
        # Validate duration
        if 'duration_value' in medication and medication['duration_value'] is not None:
            try:
                duration = int(medication['duration_value'])
                if duration < 0:
                    errors.append(f"Duration cannot be negative: {duration}")
            except (ValueError, TypeError):
                errors.append(f"Invalid duration format: {medication.get('duration_value')}")
        
        return len(errors) == 0, errors
    
    def validate_diagnosis(self, diagnosis: Dict) -> Tuple[bool, List[str]]:
        """Validate a diagnosis entity.
        
        Args:
            diagnosis: Diagnosis dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate certainty
        if 'diagnostic_certainty' in diagnosis and diagnosis['diagnostic_certainty']:
            if not self.validate_certainty(diagnosis['diagnostic_certainty']):
                errors.append(f"Invalid certainty: {diagnosis['diagnostic_certainty']}")
        
        return len(errors) == 0, errors
    
    def validate_vital_signs(self, vital_signs: Dict) -> Tuple[bool, List[str]]:
        """Validate vital signs measurements.
        
        Args:
            vital_signs: Vital signs dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate temperature (if present, should be reasonable)
        if 'temperature_celsius' in vital_signs and vital_signs['temperature_celsius'] is not None:
            try:
                temp = float(vital_signs['temperature_celsius'])
                if temp < 30 or temp > 45:
                    errors.append(f"Temperature out of reasonable range: {temp}°C")
            except (ValueError, TypeError):
                errors.append(f"Invalid temperature format: {vital_signs.get('temperature_celsius')}")
        
        # Validate heart rate
        if 'heart_rate_bpm' in vital_signs and vital_signs['heart_rate_bpm'] is not None:
            try:
                hr = int(vital_signs['heart_rate_bpm'])
                if hr < 30 or hr > 250:
                    errors.append(f"Heart rate out of reasonable range: {hr} bpm")
            except (ValueError, TypeError):
                errors.append(f"Invalid heart rate format: {vital_signs.get('heart_rate_bpm')}")
        
        # Validate oxygen saturation
        if 'oxygen_saturation_percent' in vital_signs and vital_signs['oxygen_saturation_percent'] is not None:
            try:
                o2 = float(vital_signs['oxygen_saturation_percent'])
                if o2 < 0 or o2 > 100:
                    errors.append(f"Oxygen saturation out of range: {o2}%")
            except (ValueError, TypeError):
                errors.append(f"Invalid oxygen saturation format: {vital_signs.get('oxygen_saturation_percent')}")
        
        return len(errors) == 0, errors
    
    def validate_all(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate all data and return errors.
        
        Args:
            data: Dictionary of all extracted data
            
        Returns:
            Tuple of (is_valid, list of all error messages)
        """
        all_errors = []
        
        # Validate symptoms
        for symptom in data.get('symptoms', []):
            is_valid, errors = self.validate_symptom(symptom)
            if not is_valid:
                all_errors.extend([f"Symptom: {e}" for e in errors])
        
        # Validate medications
        for medication in data.get('medications', []):
            is_valid, errors = self.validate_medication(medication)
            if not is_valid:
                all_errors.extend([f"Medication: {e}" for e in errors])
        
        # Validate diagnoses
        for diagnosis in data.get('diagnoses', []):
            is_valid, errors = self.validate_diagnosis(diagnosis)
            if not is_valid:
                all_errors.extend([f"Diagnosis: {e}" for e in errors])
        
        # Validate vital signs
        for vital_signs in data.get('vital_signs', []):
            is_valid, errors = self.validate_vital_signs(vital_signs)
            if not is_valid:
                all_errors.extend([f"Vital Signs: {e}" for e in errors])
        
        # Log warnings
        for error in all_errors:
            logger.warning(f"Validation warning: {error}")
        
        # Return True even if there are warnings (non-blocking validation)
        return True, all_errors
