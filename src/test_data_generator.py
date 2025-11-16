"""Test data generation for GP Consultation Extractor.

This module generates realistic test data for patients and doctors,
including valid NHS numbers with checksum validation.
"""

import random
from uuid import uuid4, UUID
from typing import Dict


class TestDataGenerator:
    """Generates realistic test data for patients and doctors."""
    
    # UK-specific sample data
    FIRST_NAMES = [
        'James', 'Oliver', 'George', 'Harry', 'Jack', 'Jacob', 'Charlie', 'Thomas',
        'Emily', 'Olivia', 'Amelia', 'Isla', 'Ava', 'Jessica', 'Poppy', 'Sophie',
        'Mohammed', 'Ali', 'Aisha', 'Fatima', 'Yusuf', 'Ibrahim'
    ]
    
    LAST_NAMES = [
        'Smith', 'Jones', 'Williams', 'Taylor', 'Brown', 'Davies', 'Evans', 'Wilson',
        'Thomas', 'Johnson', 'Roberts', 'Robinson', 'Thompson', 'Wright', 'Walker',
        'White', 'Edwards', 'Hughes', 'Green', 'Hall', 'Lewis', 'Clarke', 'Patel',
        'Khan', 'Ahmed', 'Ali', 'Shah'
    ]
    
    STREETS = [
        'High Street', 'Station Road', 'Main Street', 'Church Lane', 'Manor Road',
        'Park Road', 'Victoria Road', 'Green Lane', 'Mill Lane', 'Queens Road',
        'London Road', 'King Street', 'The Avenue', 'North Street', 'South Street'
    ]
    
    CITIES = [
        'London', 'Birmingham', 'Manchester', 'Leeds', 'Liverpool', 'Sheffield',
        'Bristol', 'Newcastle', 'Nottingham', 'Leicester', 'Coventry', 'Bradford',
        'Cardiff', 'Edinburgh', 'Glasgow', 'Belfast'
    ]
    
    POSTCODES = [
        'SW1A 1AA', 'M1 1AE', 'B1 1AA', 'LS1 1AA', 'L1 1AA', 'S1 1AA',
        'BS1 1AA', 'NE1 1AA', 'NG1 1AA', 'LE1 1AA', 'CV1 1AA', 'BD1 1AA'
    ]
    
    SPECIALTIES = [
        'General Practice', 'Internal Medicine', 'Family Medicine',
        'Emergency Medicine', 'Pediatrics', 'Geriatrics'
    ]
    
    def __init__(self):
        """Initialize test data generator with consistent random seed for reproducibility."""
        # Use a fixed seed for consistent test data generation
        random.seed(42)
    
    def generate_patient(self) -> Dict:
        """Generate sample patient data with realistic UK information.
        
        Returns:
            Dictionary containing patient data with keys:
            - patient_id: UUID
            - nhs_number: Valid 10-digit NHS number with checksum
            - first_name: UK first name
            - last_name: UK last name
            - date_of_birth: ISO date string
            - gender: 'M', 'F', or 'Other'
            - address: UK address
            - phone: UK phone number
            - email: Email address
        """
        patient_id = uuid4()
        first_name = random.choice(self.FIRST_NAMES)
        last_name = random.choice(self.LAST_NAMES)
        
        return {
            'patient_id': str(patient_id),  # Convert UUID to string for consistency
            'nhs_number': self.generate_nhs_number(),
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': self._generate_date_of_birth(),
            'gender': random.choice(['M', 'F', 'Other']),
            'address': self._generate_address(),
            'phone': self._generate_phone(),
            'email': f"{first_name.lower()}.{last_name.lower()}@example.com"
        }
    
    def generate_doctor(self) -> Dict:
        """Generate sample doctor data with specialty information.
        
        Returns:
            Dictionary containing doctor data with keys:
            - doctor_id: UUID
            - gmc_number: General Medical Council registration number
            - first_name: UK first name
            - last_name: UK last name
            - specialty: Medical specialty
            - practice_name: GP practice name
            - practice_address: UK address
            - phone: UK phone number
            - email: Email address
        """
        doctor_id = uuid4()
        first_name = random.choice(self.FIRST_NAMES)
        last_name = random.choice(self.LAST_NAMES)
        
        return {
            'doctor_id': str(doctor_id),  # Convert UUID to string for consistency
            'gmc_number': self._generate_gmc_number(),
            'first_name': first_name,
            'last_name': last_name,
            'specialty': random.choice(self.SPECIALTIES),
            'practice_name': f"{last_name} Medical Centre",
            'practice_address': self._generate_address(),
            'phone': self._generate_phone(),
            'email': f"dr.{first_name.lower()}.{last_name.lower()}@nhs.uk"
        }
    
    def generate_nhs_number(self) -> str:
        """Generate valid NHS number with checksum validation.
        
        NHS numbers are 10 digits with the last digit being a checksum.
        The checksum is calculated using the Modulus 11 algorithm.
        
        Returns:
            Valid 10-digit NHS number as string
        """
        # Generate first 9 digits
        digits = [random.randint(0, 9) for _ in range(9)]
        
        # Calculate checksum using Modulus 11 algorithm
        checksum = self._calculate_nhs_checksum(digits)
        
        # If checksum is 10, regenerate (invalid NHS number)
        while checksum == 10:
            digits = [random.randint(0, 9) for _ in range(9)]
            checksum = self._calculate_nhs_checksum(digits)
        
        # Append checksum
        digits.append(checksum)
        
        # Format as string
        return ''.join(map(str, digits))
    
    def _calculate_nhs_checksum(self, digits: list) -> int:
        """Calculate NHS number checksum using Modulus 11 algorithm.
        
        Args:
            digits: List of 9 digits
            
        Returns:
            Checksum digit (0-10, where 10 is invalid)
        """
        # Multiply each digit by its weight (11 - position)
        weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        total = sum(d * w for d, w in zip(digits, weights))
        
        # Calculate checksum
        remainder = total % 11
        checksum = 11 - remainder
        
        # If checksum is 11, use 0
        if checksum == 11:
            checksum = 0
        
        return checksum
    
    def _generate_date_of_birth(self) -> str:
        """Generate realistic date of birth (18-90 years old).
        
        Returns:
            ISO date string (YYYY-MM-DD)
        """
        year = random.randint(1934, 2006)  # 18-90 years old in 2024
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Use 28 to avoid month-specific logic
        
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def _generate_address(self) -> str:
        """Generate realistic UK address.
        
        Returns:
            Formatted UK address string
        """
        number = random.randint(1, 200)
        street = random.choice(self.STREETS)
        city = random.choice(self.CITIES)
        postcode = random.choice(self.POSTCODES)
        
        return f"{number} {street}, {city}, {postcode}"
    
    def _generate_phone(self) -> str:
        """Generate realistic UK phone number.
        
        Returns:
            UK phone number in format +44 XXXX XXXXXX
        """
        area_code = random.randint(1000, 9999)
        number = random.randint(100000, 999999)
        
        return f"+44 {area_code} {number}"
    
    def _generate_gmc_number(self) -> str:
        """Generate General Medical Council registration number.
        
        Returns:
            7-digit GMC number as string
        """
        return str(random.randint(1000000, 9999999))
