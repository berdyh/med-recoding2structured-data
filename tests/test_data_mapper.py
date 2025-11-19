"""Unit tests for DataMapper."""

# pylint: disable=redefined-outer-name,protected-access

import uuid
from datetime import datetime

import pandas as pd
import pytest

from data_mapper import DataMapper


@pytest.fixture
def mapper():
    """Create a DataMapper instance for testing."""
    consultation_session_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    return DataMapper(consultation_session_id, patient_id, doctor_id)


class TestDataMapperMapping:
    """Tests covering mapping logic and table generation."""

    def test_initialization(self, mapper):
        """Test DataMapper initialization."""
        assert isinstance(mapper.consultation_session_id, uuid.UUID)
        assert isinstance(mapper.patient_id, uuid.UUID)
        assert isinstance(mapper.doctor_id, uuid.UUID)
        assert isinstance(mapper.timestamp, datetime)

    def test_generate_uuid(self, mapper):
        """Test UUID generation."""
        uuid1 = mapper._generate_uuid()
        uuid2 = mapper._generate_uuid()

        # UUIDs should be strings
        assert isinstance(uuid1, str)
        assert isinstance(uuid2, str)

        # UUIDs should be unique
        assert uuid1 != uuid2

        # UUIDs should be valid format
        uuid.UUID(uuid1)  # Should not raise exception
        uuid.UUID(uuid2)

    def test_get_timestamp(self, mapper):
        """Test timestamp generation."""
        timestamp = mapper._get_timestamp()

        assert isinstance(timestamp, str)
        # Should be ISO 8601 format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_group_entities_by_attribute(self, mapper):
        """Test entity grouping by attribute."""
        entities = [
            {"class": "medication", "text": "Aspirin", "attributes": {"medication_group": "med_1"}},
            {"class": "dosage", "text": "100mg", "attributes": {"medication_group": "med_1"}},
            {
                "class": "medication",
                "text": "Ibuprofen",
                "attributes": {"medication_group": "med_2"},
            },
        ]

        groups = mapper._group_entities_by_attribute(entities, "medication_group")

        assert len(groups) == 2
        assert "med_1" in groups
        assert "med_2" in groups
        assert len(groups["med_1"]) == 2
        assert len(groups["med_2"]) == 1

    def test_map_symptoms_empty(self, mapper):
        """Test symptom mapping with empty input."""
        df = mapper.map_symptoms([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "symptom_id" in df.columns
        assert "consultation_session_id" in df.columns
        assert "patient_id" in df.columns
        assert "symptom_name" in df.columns

    def test_map_symptoms_with_data(self, mapper):
        """Test symptom mapping with data."""
        symptoms = [
            {"class": "symptom_name", "text": "headache", "attributes": {"symptom_group": "sym_1"}},
            {"class": "severity", "text": "moderate", "attributes": {"symptom_group": "sym_1"}},
            {"class": "duration", "text": "two weeks", "attributes": {"symptom_group": "sym_1"}},
        ]

        df = mapper.map_symptoms(symptoms)

        assert len(df) == 1
        assert df.iloc[0]["symptom_name"] == "headache"
        assert df.iloc[0]["severity"] == "moderate"
        assert df.iloc[0]["consultation_session_id"] == str(mapper.consultation_session_id)

    def test_map_medications_empty(self, mapper):
        """Test medication mapping with empty input."""
        df = mapper.map_medications([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "prescription_id" in df.columns
        assert "medication_name" in df.columns

    def test_map_medications_with_data(self, mapper):
        """Test medication mapping with data."""
        medications = [
            {"class": "medication", "text": "Aspirin", "attributes": {"medication_group": "med_1"}},
            {"class": "dosage", "text": "100mg", "attributes": {"medication_group": "med_1"}},
            {"class": "frequency", "text": "daily", "attributes": {"medication_group": "med_1"}},
        ]

        df = mapper.map_medications(medications)

        assert len(df) == 1
        assert df.iloc[0]["medication_name"] == "Aspirin"
        assert df.iloc[0]["dosage_value"] == 100.0
        assert df.iloc[0]["dosage_unit"] == "mg"
        assert df.iloc[0]["frequency"] == "daily"

    def test_map_diagnoses_empty(self, mapper):
        """Test diagnosis mapping with empty input."""
        diagnoses_df, assessment_df = mapper.map_diagnoses([])

        assert isinstance(diagnoses_df, pd.DataFrame)
        assert isinstance(assessment_df, pd.DataFrame)
        assert len(diagnoses_df) == 0
        assert len(assessment_df) == 0

    def test_map_diagnoses_with_data(self, mapper):
        """Test diagnosis mapping with data."""
        diagnoses = [
            {
                "class": "diagnosis",
                "text": "acute back strain",
                "attributes": {"diagnosis_group": "diag_1"},
            },
            {"class": "certainty", "text": "probable", "attributes": {"diagnosis_group": "diag_1"}},
        ]

        diagnoses_df, assessment_df = mapper.map_diagnoses(diagnoses)

        assert len(diagnoses_df) == 1
        assert len(assessment_df) == 1
        assert diagnoses_df.iloc[0]["diagnosis_name"] == "acute back strain"
        assert diagnoses_df.iloc[0]["diagnostic_certainty"] == "probable"

    def test_map_vital_signs_empty(self, mapper):
        """Test vital signs mapping with empty input."""
        df = mapper.map_vital_signs([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "vital_sign_id" in df.columns

    def test_map_vital_signs_with_data(self, mapper):
        """Test vital signs mapping with data."""
        vitals = [
            {"class": "temperature", "text": "38.2°C"},
            {"class": "blood_pressure", "text": "120/80"},
            {"class": "heart_rate", "text": "78 bpm"},
        ]

        df = mapper.map_vital_signs(vitals)

        assert len(df) == 1
        assert df.iloc[0]["temperature"] == 38.2
        assert df.iloc[0]["blood_pressure"] == "120/80"
        assert df.iloc[0]["heart_rate"] == 78

    def test_map_physical_exam_empty(self, mapper):
        """Test physical exam mapping with empty input."""
        df = mapper.map_physical_exam([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_map_red_flags_empty(self, mapper):
        """Test red flags mapping with empty input."""
        df = mapper.map_red_flags([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_map_follow_up_empty(self, mapper):
        """Test follow-up mapping with empty input."""
        df = mapper.map_follow_up([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_generate_consultation_session(self, mapper):
        """Test consultation session generation."""
        transcript = "Patient: I have a headache. GP: How long?"
        metadata = {"session_start_datetime": "2024-01-15T10:00:00Z"}

        df = mapper.generate_consultation_session(transcript, metadata)

        assert len(df) == 1
        assert df.iloc[0]["full_transcript"] == transcript
        # Use bool() to handle numpy bool types
        assert bool(df.iloc[0]["nlp_processed_flag"]) is True
        assert df.iloc[0]["consultation_session_id"] == str(mapper.consultation_session_id)

    def test_generate_consultation(self, mapper):
        """Test consultation generation."""
        metadata = {
            "consultation_datetime": "2024-01-15T10:00:00Z",
            "consultation_type": "GP Consultation",
        }

        df = mapper.generate_consultation(metadata)

        assert len(df) == 1
        assert df.iloc[0]["consultation_type"] == "GP Consultation"
        assert df.iloc[0]["consultation_session_id"] == str(mapper.consultation_session_id)

    def test_foreign_key_consistency(self, mapper):
        """Test that foreign keys are consistent across tables."""
        symptoms = [
            {"class": "symptom_name", "text": "headache", "attributes": {"symptom_group": "sym_1"}},
        ]
        medications = [
            {"class": "medication", "text": "Aspirin", "attributes": {"medication_group": "med_1"}},
        ]

        symptoms_df = mapper.map_symptoms(symptoms)
        medications_df = mapper.map_medications(medications)

        # All should have same consultation_session_id and patient_id
        assert symptoms_df.iloc[0]["consultation_session_id"] == str(mapper.consultation_session_id)
        assert symptoms_df.iloc[0]["patient_id"] == str(mapper.patient_id)
        assert medications_df.iloc[0]["consultation_session_id"] == str(
            mapper.consultation_session_id
        )
        assert medications_df.iloc[0]["patient_id"] == str(mapper.patient_id)
        assert medications_df.iloc[0]["doctor_id"] == str(mapper.doctor_id)


class TestDataMapperParsing:
    """Tests for DataMapper parsing helpers."""

    def test_parse_duration(self, mapper):
        """Test duration parsing."""
        assert mapper._parse_duration("two weeks") == 14
        assert mapper._parse_duration("3 days") == 3
        assert mapper._parse_duration("one month") == 30
        assert mapper._parse_duration("5 weeks") == 35

    def test_parse_date(self, mapper):
        """Test date parsing."""
        yesterday = mapper._parse_date("yesterday")
        assert yesterday is not None

        today = mapper._parse_date("today")
        assert today is not None

        iso_date = mapper._parse_date("2024-01-15")
        assert iso_date == "2024-01-15"

    def test_parse_dosage(self, mapper):
        """Test dosage parsing."""
        value, unit = mapper._parse_dosage("100mg")
        assert value == 100.0
        assert unit == "mg"

        value, unit = mapper._parse_dosage("2.5 tablets")
        assert value == 2.5
        assert unit == "tablets"

    def test_parse_duration_with_unit(self, mapper):
        """Test duration parsing with unit."""
        value, unit = mapper._parse_duration_with_unit("10 days")
        assert value == 10
        assert unit == "days"

        value, unit = mapper._parse_duration_with_unit("2 weeks")
        assert value == 2
        assert unit == "weeks"

    def test_normalize_certainty(self, mapper):
        """Test certainty normalization."""
        assert mapper._normalize_certainty("confirmed") == "confirmed"
        assert mapper._normalize_certainty("likely") == "probable"
        assert mapper._normalize_certainty("possible") == "suspected"
        assert mapper._normalize_certainty("rule out") == "ruled_out"

    def test_parse_temperature(self, mapper):
        """Test temperature parsing."""
        temp = mapper._parse_temperature("38.2°C")
        assert temp == 38.2

        temp = mapper._parse_temperature("100.4°F")
        assert abs(temp - 38.0) < 0.5

    def test_parse_numeric(self, mapper):
        """Test numeric parsing."""
        assert mapper._parse_numeric("78 bpm") == 78
        assert mapper._parse_numeric("98%") == 98
        assert mapper._parse_numeric("no number") is None
