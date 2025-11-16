"""Main application entry point for GP Consultation Data Extraction System.

This module orchestrates the extraction pipeline from input to CSV output.
"""

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from config_manager import ConfigManager
from llm_provider import LLMProviderManager, LLMProviderError
from input_handler import InputHandler
from entity_extractor import ClinicalEntityExtractor, ExtractionError
from data_mapper import DataMapper
from csv_exporter import CSVExporter
from validator import Validator
from test_data_generator import TestDataGenerator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# Exit codes
EXIT_SUCCESS = 0
EXIT_INPUT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_EXTRACTION_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_EXPORT_ERROR = 5


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='GP Consultation Data Extraction System'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input consultation Markdown file'
    )
    
    parser.add_argument(
        '--use-test-data',
        action='store_true',
        help='Generate test patient and doctor data automatically'
    )
    
    parser.add_argument(
        '--patient-id',
        type=str,
        help='Patient UUID (if not using test data)'
    )
    
    parser.add_argument(
        '--doctor-id',
        type=str,
        help='Doctor UUID (if not using test data)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory for CSV files (default: output)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    return parser.parse_args()


def _initialize_config(config_path: str):
    """Initialize and validate configuration.
    
    Returns:
        ConfigManager instance or None if failed
    """
    try:
        config = ConfigManager(config_path)
        if not config.validate():
            logger.error("Configuration validation failed")
            return None
        return config
    except (ValueError, IOError, OSError) as e:
        logger.error('Configuration error: %s', e)
        return None


def _initialize_llm_provider(config):
    """Initialize LLM provider.
    
    Returns:
        LLMProviderManager instance or None if failed
    """
    try:
        llm_provider = LLMProviderManager(config)
        if not llm_provider.validate_credentials():
            logger.error("LLM provider credential validation failed")
            return None
        logger.info('Using LLM provider: %s', llm_provider.get_provider())
        return llm_provider
    except LLMProviderError as e:
        logger.error('LLM provider error: %s', e)
        return None


def _read_input_file(input_path: str):
    """Read and validate input file.
    
    Returns:
        Transcript string or None if failed
    """
    try:
        input_handler = InputHandler()
        transcript = input_handler.read_transcript(input_path)

        if not input_handler.validate_format(transcript):
            logger.error("Input file format validation failed")
            return None

        logger.info('Successfully read transcript (%d characters)', len(transcript))
        return transcript
    except (IOError, OSError, ValueError) as e:
        logger.error('Input error: %s', e)
        return None


def _get_patient_doctor_ids(args):
    """Get patient and doctor IDs from args or generate test data.
    
    Returns:
        Tuple of (patient_id, doctor_id) or (None, None) if failed
    """
    if args.use_test_data:
        logger.info("Generating test patient and doctor data...")
        test_generator = TestDataGenerator()
        patient_data = test_generator.generate_patient()
        doctor_data = test_generator.generate_doctor()
        patient_id = uuid.UUID(patient_data['patient_id'])
        doctor_id = uuid.UUID(doctor_data['doctor_id'])
        logger.info('Generated test patient ID: %s', patient_id)
        logger.info('Generated test doctor ID: %s', doctor_id)
        return patient_id, doctor_id
    else:
        if not args.patient_id or not args.doctor_id:
            logger.error("Patient ID and Doctor ID are required when not using test data")
            return None, None

        try:
            patient_id = uuid.UUID(args.patient_id)
            doctor_id = uuid.UUID(args.doctor_id)
            return patient_id, doctor_id
        except ValueError as e:
            logger.error('Invalid UUID format: %s', e)
            return None, None


def _map_all_entities(mapper, extracted_entities, transcript):
    """Map all extracted entities to database schema.
    
    Returns:
        Dictionary of mapped data or None if failed
    """
    try:
        mapped_data = {}
        current_timestamp = datetime.utcnow().isoformat() + 'Z'

        # Map consultation session
        mapped_data['consultation_sessions'] = mapper.generate_consultation_session(
            transcript,
            {'session_start_datetime': current_timestamp}
        )

        # Map consultation
        mapped_data['consultations'] = mapper.generate_consultation({
            'consultation_datetime': current_timestamp,
            'consultation_type': 'GP Consultation'
        })

        # Map all entity types
        mapped_data['symptoms'] = mapper.map_symptoms(extracted_entities.get('symptoms', []))
        mapped_data['medications'] = mapper.map_medications(extracted_entities.get('medications', []))
        diagnoses_df, assessment_df = mapper.map_diagnoses(extracted_entities.get('diagnoses', []))
        mapped_data['diagnoses'] = diagnoses_df
        mapped_data['clinical_assessment_extracted'] = assessment_df
        mapped_data['vital_signs'] = mapper.map_vital_signs(extracted_entities.get('vital_signs', []))
        mapped_data['physical_examination_findings'] = mapper.map_physical_exam(
            extracted_entities.get('physical_exam', [])
        )
        mapped_data['red_flags_and_warnings'] = mapper.map_red_flags(
            extracted_entities.get('red_flags', [])
        )
        mapped_data['follow_up_plan_extracted'] = mapper.map_follow_up(
            extracted_entities.get('follow_up', [])
        )

        logger.info('Mapped %d tables', len(mapped_data))
        return mapped_data
    except (ValueError, AttributeError, IOError) as e:
        logger.error('Mapping error: %s', e)
        return None


def main():
    """Main application entry point."""
    start_time = time.time()

    try:
        args = parse_arguments()
        logger.info("Starting GP Consultation Data Extraction System")
        logger.info('Input file: %s', args.input)

        # Initialize configuration
        logger.info("Loading configuration...")
        config = _initialize_config(args.config)
        if not config:
            return EXIT_CONFIG_ERROR

        # Initialize LLM provider
        logger.info("Initializing LLM provider...")
        llm_provider = _initialize_llm_provider(config)
        if not llm_provider:
            return EXIT_CONFIG_ERROR

        # Read input file
        logger.info("Reading input file...")
        transcript = _read_input_file(args.input)
        if not transcript:
            return EXIT_INPUT_ERROR

        # Get patient/doctor IDs
        patient_id, doctor_id = _get_patient_doctor_ids(args)
        if not patient_id or not doctor_id:
            return EXIT_INPUT_ERROR

        # Generate consultation session ID
        consultation_session_id = uuid.uuid4()
        logger.info('Consultation session ID: %s', consultation_session_id)

        # Extract entities
        logger.info("Extracting clinical entities...")
        try:
            extractor = ClinicalEntityExtractor(llm_provider)
            extracted_entities = extractor.extract_all(transcript)
            total_entities = sum(len(entities) for entities in extracted_entities.values())
            logger.info('Extracted %d entities', total_entities)
            for entity_type, entities in extracted_entities.items():
                logger.info('  - %s: %d entities', entity_type, len(entities))
        except ExtractionError as e:
            logger.error('Extraction error: %s', e)
            return EXIT_EXTRACTION_ERROR

        # Validate extracted data
        logger.info("Validating extracted data...")
        try:
            validator = Validator()
            is_valid, validation_errors = validator.validate_all(extracted_entities)
            if validation_errors:
                logger.warning('Found %d validation warnings:', len(validation_errors))
                for error in validation_errors[:10]:
                    logger.warning('  - %s', error)
                if len(validation_errors) > 10:
                    logger.warning('  ... and %d more', len(validation_errors) - 10)
        except (ValueError, AttributeError) as e:
            logger.error('Validation error: %s', e)

        # Map entities to database schema
        logger.info("Mapping entities to database schema...")
        mapper = DataMapper(consultation_session_id, patient_id, doctor_id)
        mapped_data = _map_all_entities(mapper, extracted_entities, transcript)
        if not mapped_data:
            return EXIT_EXTRACTION_ERROR

        # Export CSVs
        logger.info("Exporting CSV files...")
        try:
            exporter = CSVExporter(args.output_dir)
            file_paths = exporter.export_all(mapped_data)
            processing_time = time.time() - start_time
            manifest_path = exporter.create_manifest(
                str(consultation_session_id),
                total_entities,
                processing_time
            )
            logger.info('Exported %d CSV files to %s', len(file_paths), args.output_dir)
            logger.info('Manifest file: %s', manifest_path)
        except (IOError, OSError) as e:
            logger.error('Export error: %s', e)
            return EXIT_EXPORT_ERROR

        # Success
        processing_time = time.time() - start_time
        logger.info('Processing complete in %.2f seconds', processing_time)
        logger.info('Total entities extracted: %d', total_entities)

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return EXIT_EXTRACTION_ERROR

    except (ValueError, IOError, OSError, AttributeError, RuntimeError) as e:
        logger.error('Unexpected error: %s', e, exc_info=True)
        return EXIT_EXTRACTION_ERROR


if __name__ == '__main__':
    sys.exit(main())
