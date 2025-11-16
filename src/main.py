"""Main application entry point for GP Consultation Data Extraction System.

This module orchestrates the extraction pipeline from input to CSV output.
"""

import argparse
import logging
import sys
import time
import uuid
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


def main():
    """Main application entry point."""
    start_time = time.time()
    
    try:
        # Parse arguments
        args = parse_arguments()
        logger.info("Starting GP Consultation Data Extraction System")
        logger.info(f"Input file: {args.input}")
        
        # Initialize configuration
        logger.info("Loading configuration...")
        try:
            config = ConfigManager(args.config)
            if not config.validate():
                logger.error("Configuration validation failed")
                return EXIT_CONFIG_ERROR
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return EXIT_CONFIG_ERROR
        
        # Initialize LLM provider
        logger.info("Initializing LLM provider...")
        try:
            llm_provider = LLMProviderManager(config)
            if not llm_provider.validate_credentials():
                logger.error("LLM provider credential validation failed")
                return EXIT_CONFIG_ERROR
            logger.info(f"Using LLM provider: {llm_provider.get_provider()}")
        except LLMProviderError as e:
            logger.error(f"LLM provider error: {e}")
            return EXIT_CONFIG_ERROR
        
        # Read input file
        logger.info("Reading input file...")
        try:
            input_handler = InputHandler()
            transcript = input_handler.read_transcript(args.input)
            
            if not input_handler.validate_format(transcript):
                logger.error("Input file format validation failed")
                return EXIT_INPUT_ERROR
            
            logger.info(f"Successfully read transcript ({len(transcript)} characters)")
        except Exception as e:
            logger.error(f"Input error: {e}")
            return EXIT_INPUT_ERROR
        
        # Generate or load patient/doctor data
        if args.use_test_data:
            logger.info("Generating test patient and doctor data...")
            test_generator = TestDataGenerator()
            patient_data = test_generator.generate_patient()
            doctor_data = test_generator.generate_doctor()
            patient_id = uuid.UUID(patient_data['patient_id'])
            doctor_id = uuid.UUID(doctor_data['doctor_id'])
            logger.info(f"Generated test patient ID: {patient_id}")
            logger.info(f"Generated test doctor ID: {doctor_id}")
        else:
            if not args.patient_id or not args.doctor_id:
                logger.error("Patient ID and Doctor ID are required when not using test data")
                return EXIT_INPUT_ERROR
            
            try:
                patient_id = uuid.UUID(args.patient_id)
                doctor_id = uuid.UUID(args.doctor_id)
            except ValueError as e:
                logger.error(f"Invalid UUID format: {e}")
                return EXIT_INPUT_ERROR
        
        # Generate consultation session ID
        consultation_session_id = uuid.uuid4()
        logger.info(f"Consultation session ID: {consultation_session_id}")
        
        # Extract entities
        logger.info("Extracting clinical entities...")
        try:
            extractor = ClinicalEntityExtractor(llm_provider)
            extracted_entities = extractor.extract_all(transcript)
            
            total_entities = sum(len(entities) for entities in extracted_entities.values())
            logger.info(f"Extracted {total_entities} entities")
            
            for entity_type, entities in extracted_entities.items():
                logger.info(f"  - {entity_type}: {len(entities)} entities")
        
        except ExtractionError as e:
            logger.error(f"Extraction error: {e}")
            return EXIT_EXTRACTION_ERROR
        
        # Validate extracted data
        logger.info("Validating extracted data...")
        try:
            validator = Validator()
            is_valid, validation_errors = validator.validate_all(extracted_entities)
            
            if validation_errors:
                logger.warning(f"Found {len(validation_errors)} validation warnings:")
                for error in validation_errors[:10]:  # Show first 10
                    logger.warning(f"  - {error}")
                if len(validation_errors) > 10:
                    logger.warning(f"  ... and {len(validation_errors) - 10} more")
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            # Continue processing despite validation errors
        
        # Map entities to database schema
        logger.info("Mapping entities to database schema...")
        try:
            mapper = DataMapper(consultation_session_id, patient_id, doctor_id)
            
            mapped_data = {}
            
            # Map consultation session
            mapped_data['consultation_sessions'] = mapper.generate_consultation_session(
                transcript,
                {'session_start_datetime': mapper._get_timestamp()}
            )
            
            # Map consultation
            mapped_data['consultations'] = mapper.generate_consultation({
                'consultation_datetime': mapper._get_timestamp(),
                'consultation_type': 'GP Consultation'
            })
            
            # Map symptoms
            mapped_data['symptoms'] = mapper.map_symptoms(extracted_entities.get('symptoms', []))
            
            # Map medications
            mapped_data['medications'] = mapper.map_medications(extracted_entities.get('medications', []))
            
            # Map diagnoses (returns tuple of diagnoses and clinical assessment)
            diagnoses_df, assessment_df = mapper.map_diagnoses(extracted_entities.get('diagnoses', []))
            mapped_data['diagnoses'] = diagnoses_df
            mapped_data['clinical_assessment_extracted'] = assessment_df
            
            # Map vital signs
            mapped_data['vital_signs'] = mapper.map_vital_signs(extracted_entities.get('vital_signs', []))
            
            # Map physical exam
            mapped_data['physical_examination_findings'] = mapper.map_physical_exam(
                extracted_entities.get('physical_exam', [])
            )
            
            # Map red flags
            mapped_data['red_flags_and_warnings'] = mapper.map_red_flags(
                extracted_entities.get('red_flags', [])
            )
            
            # Map follow-up
            mapped_data['follow_up_plan_extracted'] = mapper.map_follow_up(
                extracted_entities.get('follow_up', [])
            )
            
            logger.info(f"Mapped {len(mapped_data)} tables")
        
        except Exception as e:
            logger.error(f"Mapping error: {e}")
            return EXIT_EXTRACTION_ERROR
        
        # Export CSVs
        logger.info("Exporting CSV files...")
        try:
            exporter = CSVExporter(args.output_dir)
            file_paths = exporter.export_all(mapped_data)
            
            # Create manifest
            processing_time = time.time() - start_time
            manifest_path = exporter.create_manifest(
                str(consultation_session_id),
                total_entities,
                processing_time
            )
            
            logger.info(f"Exported {len(file_paths)} CSV files to {args.output_dir}")
            logger.info(f"Manifest file: {manifest_path}")
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            return EXIT_EXPORT_ERROR
        
        # Success
        processing_time = time.time() - start_time
        logger.info(f"Processing complete in {processing_time:.2f} seconds")
        logger.info(f"Total entities extracted: {total_entities}")
        
        return EXIT_SUCCESS
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return EXIT_EXTRACTION_ERROR
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return EXIT_EXTRACTION_ERROR


if __name__ == '__main__':
    sys.exit(main())
