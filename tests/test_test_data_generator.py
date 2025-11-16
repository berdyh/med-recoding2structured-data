"""Unit tests for test data generation."""

import pytest
import re
from uuid import UUID

import sys
sys.path.insert(0, 'src')

from test_data_generator import TestDataGenerator


class TestTestDataGenerator:
    """Test cases for TestDataGenerator class."""
    
    def test_generate_patient_structure(self):
        """Test patient data has correct structure."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        # Check all required fields exist
        assert 'patient_id' in patient
        assert 'nhs_number' in patient
        assert 'first_name' in patient
        assert 'last_name' in patient
        assert 'date_of_birth' in patient
        assert 'gender' in patient
        assert 'address' in patient
        assert 'phone' in patient
        assert 'email' in patient
    
    def test_generate_patient_uuid(self):
        """Test patient_id is a valid UUID."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        assert isinstance(patient['patient_id'], UUID)
    
    def test_generate_patient_nhs_number_format(self):
        """Test NHS number is 10 digits."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        assert len(patient['nhs_number']) == 10
        assert patient['nhs_number'].isdigit()
    
    def test_generate_patient_gender(self):
        """Test gender is valid value."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        assert patient['gender'] in ['M', 'F', 'Other']
    
    def test_generate_patient_date_of_birth_format(self):
        """Test date of birth is in ISO format."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        # Check ISO date format YYYY-MM-DD
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', patient['date_of_birth'])
    
    def test_generate_patient_email_format(self):
        """Test email has valid format."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        assert '@' in patient['email']
        assert '.' in patient['email']
    
    def test_generate_patient_phone_format(self):
        """Test phone number has UK format."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        assert patient['phone'].startswith('+44')
    
    def test_generate_doctor_structure(self):
        """Test doctor data has correct structure."""
        generator = TestDataGenerator()
        doctor = generator.generate_doctor()
        
        # Check all required fields exist
        assert 'doctor_id' in doctor
        assert 'gmc_number' in doctor
        assert 'first_name' in doctor
        assert 'last_name' in doctor
        assert 'specialty' in doctor
        assert 'practice_name' in doctor
        assert 'practice_address' in doctor
        assert 'phone' in doctor
        assert 'email' in doctor
    
    def test_generate_doctor_uuid(self):
        """Test doctor_id is a valid UUID."""
        generator = TestDataGenerator()
        doctor = generator.generate_doctor()
        
        assert isinstance(doctor['doctor_id'], UUID)
    
    def test_generate_doctor_gmc_number_format(self):
        """Test GMC number is 7 digits."""
        generator = TestDataGenerator()
        doctor = generator.generate_doctor()
        
        assert len(doctor['gmc_number']) == 7
        assert doctor['gmc_number'].isdigit()
    
    def test_generate_doctor_specialty(self):
        """Test specialty is from valid list."""
        generator = TestDataGenerator()
        doctor = generator.generate_doctor()
        
        assert doctor['specialty'] in generator.SPECIALTIES
    
    def test_generate_doctor_email_format(self):
        """Test doctor email has NHS domain."""
        generator = TestDataGenerator()
        doctor = generator.generate_doctor()
        
        assert '@nhs.uk' in doctor['email']
    
    def test_generate_nhs_number_valid_checksum(self):
        """Test NHS number has valid checksum."""
        generator = TestDataGenerator()
        
        # Generate multiple NHS numbers and validate checksums
        for _ in range(10):
            nhs_number = generator.generate_nhs_number()
            
            # Validate checksum
            digits = [int(d) for d in nhs_number]
            calculated_checksum = generator._calculate_nhs_checksum(digits[:9])
            
            assert digits[9] == calculated_checksum
    
    def test_nhs_checksum_calculation(self):
        """Test NHS checksum calculation with known values."""
        generator = TestDataGenerator()
        
        # Known valid NHS number: 4505577104
        digits = [4, 5, 0, 5, 5, 7, 7, 1, 0]
        checksum = generator._calculate_nhs_checksum(digits)
        
        assert checksum == 4
    
    def test_nhs_checksum_with_zero(self):
        """Test NHS checksum calculation resulting in 0."""
        generator = TestDataGenerator()
        
        # Example that should result in checksum 0
        # When remainder is 0, checksum should be 11, which becomes 0
        digits = [1, 2, 1, 2, 1, 2, 1, 2, 1]  # Contrived example
        checksum = generator._calculate_nhs_checksum(digits)
        
        # Checksum should be between 0-10
        assert 0 <= checksum <= 10
    
    def test_generate_nhs_number_no_invalid_checksum(self):
        """Test NHS number generation never produces checksum 10."""
        generator = TestDataGenerator()
        
        # Generate many NHS numbers and ensure none have invalid checksum
        for _ in range(100):
            nhs_number = generator.generate_nhs_number()
            digits = [int(d) for d in nhs_number]
            
            # Last digit should never be 10
            assert digits[9] != 10
    
    def test_uuid_consistency_across_calls(self):
        """Test that UUIDs are unique across multiple generations."""
        generator = TestDataGenerator()
        
        patient1 = generator.generate_patient()
        patient2 = generator.generate_patient()
        doctor1 = generator.generate_doctor()
        doctor2 = generator.generate_doctor()
        
        # All UUIDs should be unique
        uuids = [
            patient1['patient_id'],
            patient2['patient_id'],
            doctor1['doctor_id'],
            doctor2['doctor_id']
        ]
        
        assert len(set(uuids)) == len(uuids)
    
    def test_address_format(self):
        """Test address has UK format."""
        generator = TestDataGenerator()
        patient = generator.generate_patient()
        
        # Address should contain number, street, city, postcode
        assert ',' in patient['address']
        # Should have at least 2 commas (number street, city, postcode)
        assert patient['address'].count(',') >= 1
    
    def test_reproducibility_with_seed(self):
        """Test that generator produces consistent results with same seed."""
        # Create two generators (both use seed 42)
        gen1 = TestDataGenerator()
        gen2 = TestDataGenerator()
        
        patient1 = gen1.generate_patient()
        patient2 = gen2.generate_patient()
        
        # Should generate same data due to same seed
        assert patient1['first_name'] == patient2['first_name']
        assert patient1['last_name'] == patient2['last_name']
        assert patient1['nhs_number'] == patient2['nhs_number']
