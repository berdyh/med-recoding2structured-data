"""Database schema mapping for extracted clinical entities.

This module maps extracted entities to PostgreSQL database schema format.
"""

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


class DataMapper:
    """Maps extracted clinical entities to database schema."""

    def __init__(
        self, consultation_session_id: uuid.UUID, patient_id: uuid.UUID, doctor_id: uuid.UUID
    ):
        """Initialize data mapper with core IDs.

        Args:
            consultation_session_id: UUID for consultation session
            patient_id: UUID for patient
            doctor_id: UUID for doctor
        """
        self.consultation_session_id = consultation_session_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.timestamp = datetime.now(UTC)

    def _generate_uuid(self) -> str:
        """Generate a new UUID4 string.

        Returns:
            UUID string
        """
        return str(uuid.uuid4())

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format.

        Returns:
            ISO 8601 timestamp string
        """
        return self.timestamp.isoformat()

    def _group_entities_by_attribute(
        self, entities: list[dict], group_attr: str
    ) -> dict[str, list[dict]]:
        """Group entities by a grouping attribute.

        Args:
            entities: List of entity dictionaries
            group_attr: Attribute name to group by (e.g., 'medication_group')

        Returns:
            Dictionary mapping group ID to list of entities
        """
        groups = {}
        for entity in entities:
            attrs = entity.get("attributes", {})
            group_id = attrs.get(group_attr)

            if group_id:
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append(entity)

        return groups

    def map_symptoms(self, symptoms: list[dict]) -> pd.DataFrame:
        """Map symptoms to SYMPTOMS table format.

        Args:
            symptoms: List of symptom entities from extraction

        Returns:
            DataFrame in SYMPTOMS table format
        """
        if not symptoms:
            # Return empty DataFrame with correct schema
            return pd.DataFrame(
                columns=[
                    "symptom_id",
                    "consultation_session_id",
                    "patient_id",
                    "symptom_name",
                    "symptom_code",
                    "severity",
                    "duration_days",
                    "onset_date",
                    "temporal_pattern",
                    "confidence_score",
                    "clinical_modifiers",
                    "extracted_at",
                ]
            )

        # Group symptoms by symptom_group attribute
        symptom_groups = self._group_entities_by_attribute(symptoms, "symptom_group")

        rows = []
        for _, group_entities in symptom_groups.items():
            symptom_data = {
                "symptom_id": self._generate_uuid(),
                "consultation_session_id": str(self.consultation_session_id),
                "patient_id": str(self.patient_id),
                "symptom_name": None,
                "symptom_code": None,
                "severity": None,
                "duration_days": None,
                "onset_date": None,
                "temporal_pattern": None,
                "confidence_score": 0.8,  # Default confidence
                "clinical_modifiers": {},
                "extracted_at": self._get_timestamp(),
            }

            # Extract fields from grouped entities
            for entity in group_entities:
                entity_class = entity.get("class", "")
                entity_text = entity.get("text", "")

                if entity_class == "symptom_name":
                    symptom_data["symptom_name"] = entity_text
                elif entity_class == "severity":
                    symptom_data["severity"] = entity_text.lower()
                elif entity_class == "duration":
                    # Parse duration (e.g., "two weeks" -> 14 days)
                    symptom_data["duration_days"] = self._parse_duration(entity_text)
                elif entity_class == "onset":
                    symptom_data["onset_date"] = self._parse_date(entity_text)
                elif entity_class == "temporal_pattern":
                    symptom_data["temporal_pattern"] = entity_text

            rows.append(symptom_data)

        return pd.DataFrame(rows)

    def _parse_duration(self, duration_text: str) -> int | None:
        """Parse duration text to days.

        Args:
            duration_text: Duration text (e.g., "two weeks", "3 days")

        Returns:
            Duration in days or None
        """
        # Convert text numbers to digits
        text_to_num = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }

        duration_text_lower = duration_text.lower()

        # Extract number
        number = None
        for word, num in text_to_num.items():
            if word in duration_text_lower:
                number = num
                break

        if not number:
            # Try to extract digit
            match = re.search(r"\d+", duration_text)
            if match:
                number = int(match.group())

        if not number:
            return None

        # Determine unit
        if "week" in duration_text_lower:
            return number * 7
        if "month" in duration_text_lower:
            return number * 30
        if "day" in duration_text_lower:
            return number

        return number  # Default to days

    def _parse_date(self, date_text: str) -> str | None:
        """Parse date text to ISO 8601 format.

        Args:
            date_text: Date text (e.g., "yesterday", "2024-01-15")

        Returns:
            ISO 8601 date string or None
        """
        date_text_lower = date_text.lower()

        # Handle relative dates
        if "yesterday" in date_text_lower:
            date = datetime.now(UTC) - timedelta(days=1)
            return date.date().isoformat()
        if "today" in date_text_lower:
            return datetime.now(UTC).date().isoformat()
        if "last week" in date_text_lower:
            date = datetime.now(UTC) - timedelta(days=7)
            return date.date().isoformat()

        # Try to parse ISO format
        try:
            date = datetime.fromisoformat(date_text)
            return date.date().isoformat()
        except ValueError:
            return None

    def map_medications(self, medications: list[dict]) -> pd.DataFrame:
        """Map medications to MEDICATIONS table format.

        Args:
            medications: List of medication entities from extraction

        Returns:
            DataFrame in MEDICATIONS table format
        """
        if not medications:
            return pd.DataFrame(
                columns=[
                    "prescription_id",
                    "consultation_session_id",
                    "patient_id",
                    "doctor_id",
                    "medication_name",
                    "dosage_value",
                    "dosage_unit",
                    "frequency",
                    "duration_value",
                    "duration_unit",
                    "route_of_administration",
                    "indication",
                    "prescribed_at",
                ]
            )

        # Group medications by medication_group attribute
        med_groups = self._group_entities_by_attribute(medications, "medication_group")

        rows = []
        for _, group_entities in med_groups.items():
            med_data = {
                "prescription_id": self._generate_uuid(),
                "consultation_session_id": str(self.consultation_session_id),
                "patient_id": str(self.patient_id),
                "doctor_id": str(self.doctor_id),
                "medication_name": None,
                "dosage_value": None,
                "dosage_unit": None,
                "frequency": None,
                "duration_value": None,
                "duration_unit": None,
                "route_of_administration": None,
                "indication": None,
                "prescribed_at": self._get_timestamp(),
            }

            # Extract fields from grouped entities
            for entity in group_entities:
                entity_class = entity.get("class", "")
                entity_text = entity.get("text", "")

                if entity_class == "medication":
                    med_data["medication_name"] = entity_text
                elif entity_class == "dosage":
                    # Parse dosage (e.g., "100mg" -> value=100, unit="mg")
                    value, unit = self._parse_dosage(entity_text)
                    med_data["dosage_value"] = value
                    med_data["dosage_unit"] = unit
                elif entity_class == "route":
                    med_data["route_of_administration"] = entity_text
                elif entity_class == "frequency":
                    med_data["frequency"] = entity_text
                elif entity_class == "duration":
                    # Parse duration (e.g., "10 days" -> value=10, unit="days")
                    value, unit = self._parse_duration_with_unit(entity_text)
                    med_data["duration_value"] = value
                    med_data["duration_unit"] = unit
                elif entity_class == "indication":
                    med_data["indication"] = entity_text

            rows.append(med_data)

        return pd.DataFrame(rows)

    def _parse_dosage(self, dosage_text: str) -> tuple:
        """Parse dosage text to value and unit.

        Args:
            dosage_text: Dosage text (e.g., "100mg", "2 tablets")

        Returns:
            Tuple of (value, unit)
        """
        # Extract number
        match = re.search(r"(\d+(?:\.\d+)?)", dosage_text)
        if not match:
            return None, None

        value = float(match.group(1))

        # Extract unit
        unit_match = re.search(r"[a-zA-Z]+", dosage_text)
        unit = unit_match.group() if unit_match else None

        return value, unit

    def _parse_duration_with_unit(self, duration_text: str) -> tuple:
        """Parse duration text to value and unit.

        Args:
            duration_text: Duration text (e.g., "10 days", "2 weeks")

        Returns:
            Tuple of (value, unit)
        """
        # Extract number
        match = re.search(r"(\d+)", duration_text)
        if not match:
            return None, None

        value = int(match.group(1))

        # Determine unit
        duration_text_lower = duration_text.lower()
        if "week" in duration_text_lower:
            unit = "weeks"
        elif "month" in duration_text_lower:
            unit = "months"
        elif "day" in duration_text_lower:
            unit = "days"
        else:
            unit = "days"  # Default

        return value, unit

    def map_diagnoses(self, diagnoses: list[dict]) -> tuple:
        """Map diagnoses to DIAGNOSES and CLINICAL_ASSESSMENT_EXTRACTED tables.

        Args:
            diagnoses: List of diagnosis entities from extraction

        Returns:
            Tuple of (diagnoses_df, clinical_assessment_df)
        """
        if not diagnoses:
            diagnoses_df = pd.DataFrame(
                columns=[
                    "diagnosis_id",
                    "consultation_session_id",
                    "patient_id",
                    "doctor_id",
                    "diagnosis_name",
                    "diagnosis_code",
                    "diagnostic_certainty",
                    "clinical_notes",
                    "diagnosed_at",
                ]
            )
            assessment_df = pd.DataFrame(
                columns=[
                    "assessment_id",
                    "consultation_session_id",
                    "patient_id",
                    "doctor_id",
                    "assessment_diagnosis",
                    "diagnostic_certainty",
                    "diagnostic_reasoning",
                    "key_clinical_features_supporting",
                    "assessed_at",
                ]
            )
            return diagnoses_df, assessment_df

        # Group diagnoses by diagnosis_group attribute
        diag_groups = self._group_entities_by_attribute(diagnoses, "diagnosis_group")

        diagnoses_rows = []
        assessment_rows = []

        for _, group_entities in diag_groups.items():
            diagnosis_name = None
            certainty = None
            clinical_features = None

            # Extract fields from grouped entities
            for entity in group_entities:
                entity_class = entity.get("class", "")
                entity_text = entity.get("text", "")

                if entity_class == "diagnosis":
                    diagnosis_name = entity_text
                elif entity_class == "certainty":
                    certainty = self._normalize_certainty(entity_text)
                elif entity_class == "clinical_features":
                    clinical_features = entity_text

            # Create DIAGNOSES row
            diagnoses_rows.append(
                {
                    "diagnosis_id": self._generate_uuid(),
                    "consultation_session_id": str(self.consultation_session_id),
                    "patient_id": str(self.patient_id),
                    "doctor_id": str(self.doctor_id),
                    "diagnosis_name": diagnosis_name,
                    "diagnosis_code": None,  # Would need ICD-10 mapping
                    "diagnostic_certainty": certainty,
                    "clinical_notes": clinical_features,
                    "diagnosed_at": self._get_timestamp(),
                }
            )

            # Create CLINICAL_ASSESSMENT_EXTRACTED row
            assessment_rows.append(
                {
                    "assessment_id": self._generate_uuid(),
                    "consultation_session_id": str(self.consultation_session_id),
                    "patient_id": str(self.patient_id),
                    "doctor_id": str(self.doctor_id),
                    "assessment_diagnosis": diagnosis_name,
                    "diagnostic_certainty": certainty,
                    "diagnostic_reasoning": None,
                    "key_clinical_features_supporting": clinical_features,
                    "assessed_at": self._get_timestamp(),
                }
            )

        return pd.DataFrame(diagnoses_rows), pd.DataFrame(assessment_rows)

    def _normalize_certainty(self, certainty_text: str) -> str:
        """Normalize certainty text to standard values.

        Args:
            certainty_text: Certainty text from extraction

        Returns:
            Normalized certainty value
        """
        certainty_lower = certainty_text.lower()

        if "confirm" in certainty_lower or "definite" in certainty_lower:
            return "confirmed"
        if "probable" in certainty_lower or "likely" in certainty_lower:
            return "probable"
        if "suspect" in certainty_lower or "possible" in certainty_lower:
            return "suspected"
        if "rule" in certainty_lower and "out" in certainty_lower:
            return "ruled_out"

        return "suspected"  # Default

    def map_vital_signs(self, vitals: list[dict]) -> pd.DataFrame:
        """Map vital signs to VITAL_SIGNS table format.

        Args:
            vitals: List of vital sign entities from extraction

        Returns:
            DataFrame in VITAL_SIGNS table format
        """
        if not vitals:
            return pd.DataFrame(
                columns=[
                    "vital_sign_id",
                    "consultation_session_id",
                    "patient_id",
                    "temperature",
                    "blood_pressure",
                    "heart_rate",
                    "oxygen_saturation",
                    "respiratory_rate",
                    "measured_at",
                ]
            )

        # Vital signs are typically extracted as a group
        vital_data = {
            "vital_sign_id": self._generate_uuid(),
            "consultation_session_id": str(self.consultation_session_id),
            "patient_id": str(self.patient_id),
            "temperature": None,
            "blood_pressure": None,
            "heart_rate": None,
            "oxygen_saturation": None,
            "respiratory_rate": None,
            "measured_at": self._get_timestamp(),
        }

        # Extract fields
        for entity in vitals:
            entity_class = entity.get("class", "")
            entity_text = entity.get("text", "")

            if entity_class == "temperature":
                vital_data["temperature"] = self._parse_temperature(entity_text)
            elif entity_class == "blood_pressure":
                vital_data["blood_pressure"] = entity_text
            elif entity_class == "heart_rate":
                vital_data["heart_rate"] = self._parse_numeric(entity_text)
            elif entity_class == "oxygen_saturation":
                vital_data["oxygen_saturation"] = self._parse_numeric(entity_text)
            elif entity_class == "respiratory_rate":
                vital_data["respiratory_rate"] = self._parse_numeric(entity_text)

        return pd.DataFrame([vital_data])

    def _parse_temperature(self, temp_text: str) -> float | None:
        """Parse temperature text to float.

        Args:
            temp_text: Temperature text (e.g., "38.2°C", "100.4°F")

        Returns:
            Temperature in Celsius
        """
        match = re.search(r"(\d+(?:\.\d+)?)", temp_text)
        if not match:
            return None

        temp = float(match.group(1))

        # Convert Fahrenheit to Celsius if needed
        if "°F" in temp_text or "F" in temp_text.upper():
            temp = (temp - 32) * 5 / 9

        return temp

    def _parse_numeric(self, text: str) -> int | None:
        """Parse numeric value from text.

        Args:
            text: Text containing number

        Returns:
            Numeric value or None
        """
        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1))
        return None

    def map_physical_exam(self, exams: list[dict]) -> pd.DataFrame:
        """Map physical exam to PHYSICAL_EXAMINATION_FINDINGS table.

        Args:
            exams: List of physical exam entities from extraction

        Returns:
            DataFrame in PHYSICAL_EXAMINATION_FINDINGS table format
        """
        if not exams:
            return pd.DataFrame(
                columns=[
                    "exam_finding_id",
                    "consultation_session_id",
                    "patient_id",
                    "examination_type",
                    "anatomical_site",
                    "findings",
                    "severity",
                    "examined_at",
                ]
            )

        # Group exams by exam_group attribute
        exam_groups = self._group_entities_by_attribute(exams, "exam_group")

        rows = []
        for _, group_entities in exam_groups.items():
            exam_data = {
                "exam_finding_id": self._generate_uuid(),
                "consultation_session_id": str(self.consultation_session_id),
                "patient_id": str(self.patient_id),
                "examination_type": None,
                "anatomical_site": None,
                "findings": None,
                "severity": None,
                "examined_at": self._get_timestamp(),
            }

            # Extract fields from grouped entities
            for entity in group_entities:
                entity_class = entity.get("class", "")
                entity_text = entity.get("text", "")

                if entity_class == "examination_type":
                    exam_data["examination_type"] = entity_text
                elif entity_class == "anatomical_site":
                    exam_data["anatomical_site"] = entity_text
                elif entity_class == "findings":
                    exam_data["findings"] = entity_text
                elif entity_class == "severity":
                    exam_data["severity"] = entity_text.lower()

            rows.append(exam_data)

        return pd.DataFrame(rows)

    def map_red_flags(self, flags: list[dict]) -> pd.DataFrame:
        """Map red flags to RED_FLAGS_AND_WARNINGS table.

        Args:
            flags: List of red flag entities from extraction

        Returns:
            DataFrame in RED_FLAGS_AND_WARNINGS table format
        """
        if not flags:
            return pd.DataFrame(
                columns=[
                    "red_flag_id",
                    "consultation_session_id",
                    "patient_id",
                    "warning_description",
                    "warning_type",
                    "severity",
                    "identified_at",
                ]
            )

        # Group red flags by warning_group attribute
        flag_groups = self._group_entities_by_attribute(flags, "warning_group")

        rows = []
        for _, group_entities in flag_groups.items():
            flag_data = {
                "red_flag_id": self._generate_uuid(),
                "consultation_session_id": str(self.consultation_session_id),
                "patient_id": str(self.patient_id),
                "warning_description": None,
                "warning_type": None,
                "severity": None,
                "identified_at": self._get_timestamp(),
            }

            # Extract fields from grouped entities
            for entity in group_entities:
                entity_class = entity.get("class", "")
                entity_text = entity.get("text", "")

                if entity_class == "warning_description":
                    flag_data["warning_description"] = entity_text
                elif entity_class == "warning_type":
                    flag_data["warning_type"] = entity_text
                elif entity_class == "severity":
                    flag_data["severity"] = entity_text.lower()

            rows.append(flag_data)

        return pd.DataFrame(rows)

    def map_follow_up(self, plans: list[dict]) -> pd.DataFrame:
        """Map follow-up to FOLLOW_UP_PLAN_EXTRACTED table.

        Args:
            plans: List of follow-up entities from extraction

        Returns:
            DataFrame in FOLLOW_UP_PLAN_EXTRACTED table format
        """
        if not plans:
            return pd.DataFrame(
                columns=[
                    "follow_up_id",
                    "consultation_session_id",
                    "patient_id",
                    "follow_up_type",
                    "timing",
                    "condition",
                    "action",
                    "priority",
                    "planned_at",
                ]
            )

        # Group follow-ups by followup_group attribute
        followup_groups = self._group_entities_by_attribute(plans, "followup_group")

        rows = []
        for _, group_entities in followup_groups.items():
            followup_data = {
                "follow_up_id": self._generate_uuid(),
                "consultation_session_id": str(self.consultation_session_id),
                "patient_id": str(self.patient_id),
                "follow_up_type": None,
                "timing": None,
                "condition": None,
                "action": None,
                "priority": None,
                "planned_at": self._get_timestamp(),
            }

            # Extract fields from grouped entities
            for entity in group_entities:
                entity_class = entity.get("class", "")
                entity_text = entity.get("text", "")

                if entity_class == "follow_up_type":
                    followup_data["follow_up_type"] = entity_text
                elif entity_class == "timing":
                    followup_data["timing"] = entity_text
                elif entity_class == "condition":
                    followup_data["condition"] = entity_text
                elif entity_class == "action":
                    followup_data["action"] = entity_text
                elif entity_class == "priority":
                    followup_data["priority"] = entity_text

            rows.append(followup_data)

        return pd.DataFrame(rows)

    def generate_consultation_session(self, transcript: str, metadata: dict) -> pd.DataFrame:
        """Generate CONSULTATION_SESSIONS table row.

        Args:
            transcript: Full consultation transcript
            metadata: Additional metadata

        Returns:
            DataFrame with single row for CONSULTATION_SESSIONS table
        """
        session_data = {
            "consultation_session_id": str(self.consultation_session_id),
            "patient_id": str(self.patient_id),
            "doctor_id": str(self.doctor_id),
            "session_start_datetime": metadata.get("session_start_datetime", self._get_timestamp()),
            "full_transcript": transcript,
            "transcript_language": metadata.get("transcript_language", "en-UK"),
            "nlp_processed_flag": True,  # Explicitly convert to Python bool
            "created_at": self._get_timestamp(),
        }

        df = pd.DataFrame([session_data])
        # Ensure boolean column is Python bool, not numpy bool
        df["nlp_processed_flag"] = df["nlp_processed_flag"].astype(bool)
        return df

    def generate_consultation(self, metadata: dict) -> pd.DataFrame:
        """Generate CONSULTATIONS table row.

        Args:
            metadata: Consultation metadata

        Returns:
            DataFrame with single row for CONSULTATIONS table
        """
        consultation_data = {
            "consultation_id": self._generate_uuid(),
            "consultation_session_id": str(self.consultation_session_id),
            "patient_id": str(self.patient_id),
            "doctor_id": str(self.doctor_id),
            "consultation_datetime": metadata.get("consultation_datetime", self._get_timestamp()),
            "consultation_type": metadata.get("consultation_type", "GP Consultation"),
            "chief_complaint": metadata.get("chief_complaint", ""),
            "history_of_present_illness": metadata.get("history_of_present_illness", ""),
            "created_at": self._get_timestamp(),
        }

        return pd.DataFrame([consultation_data])
