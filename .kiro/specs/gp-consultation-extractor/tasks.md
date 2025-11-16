# Implementation Plan

This implementation plan breaks down the GP Consultation Data Extraction System into discrete, manageable coding tasks. Each task builds incrementally on previous work and references specific requirements from the requirements document.

---

- [x] 1. Set up project structure and documentation
  - Create directory structure (src/, tests/, config/, input/, output/, docs/)
  - Create README.md files for each subfolder explaining their purpose
  - Create docs/architecture.md with Mermaid database schema diagram
  - Create requirements.txt with all dependencies
  - Create .gitignore for Python project
  - _Requirements: 1.1, 13.1, 13.4, 14.1_

- [ ] 2. Implement configuration management
  - [ ] 2.1 Create ConfigManager class in config_manager.py
    - Load configuration from YAML file and environment variables
    - Implement priority order: env vars > config file > defaults
    - Add validation for required configuration parameters
    - Add blackrog aws api key as as follows #[qv0WzNJUCXyiFgFNDr7zsbjbeuvOC3dO48OAbSGFbCA]
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 14.1_

  - [ ] 2.2 Create config/config.yaml with default settings
    - Define LLM provider settings (Gemini and Bedrock)
    - Define extraction parameters (confidence threshold, retry attempts)
    - Define output settings (directory, encoding)
    - Define logging configuration
    - _Requirements: 10.1, 10.2, 10.3, 14.1_

- [ ] 3. Implement LLM provider management
  - [ ] 3.1 Create LLMProviderManager class in llm_provider.py
    - Implement provider selection logic (Gemini vs Bedrock)
    - Add credential validation for both providers
    - Implement get_provider() and get_api_credentials() methods
    - Handle AWS Bedrock configuration with boto3
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 13.3, 14.1_

  - [ ] 3.2 Write unit tests for LLMProviderManager
    - Test provider selection based on environment variables
    - Test credential validation for both providers
    - Test error handling for missing credentials
    - _Requirements: 2.4, 2.5, 14.1_

- [ ] 4. Implement input handling
  - [ ] 4.1 Create InputHandler class in input_handler.py
    - Implement read_transcript() to read Markdown files with UTF-8 encoding
    - Implement validate_format() to check for minimum required structure
    - Add error handling for file not found and encoding errors
    - _Requirements: 1.1, 1.2, 1.3, 14.1_

  - [ ] 4.2 Write unit tests for InputHandler
    - Test successful file reading
    - Test file not found error handling
    - Test format validation
    - _Requirements: 1.3, 14.1_

- [ ] 5. Implement test data generation
  - [ ] 5.1 Create TestDataGenerator class in test_data_generator.py
    - Implement generate_patient() with realistic UK data
    - Implement generate_doctor() with specialties
    - Implement generate_nhs_number() with checksum validation
    - Generate consistent UUIDs for relationships
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 14.1_

  - [ ] 5.2 Write unit tests for TestDataGenerator
    - Test NHS number generation and validation
    - Test patient data structure
    - Test doctor data structure
    - Test UUID consistency
    - _Requirements: 6.4, 14.1_

- [ ] 6. Create few-shot learning examples
  - [ ] 6.1 Create config/few_shot_examples.yaml
    - Define medication extraction examples with medication_group attributes
    - Define symptom extraction examples with symptom_group attributes
    - Define diagnosis extraction examples with diagnosis_group attributes
    - Define vital signs extraction examples
    - Define physical exam extraction examples
    - Define red flags extraction examples
    - Define follow-up plan extraction examples
    - _Requirements: 3.9, 4.1, 4.2, 4.3, 4.4, 4.5, 13.2, 14.1_

- [ ] 7. Implement clinical entity extraction
  - [ ] 7.1 Create ClinicalEntityExtractor class in entity_extractor.py
    - Initialize with LLMProviderManager
    - Load few-shot examples from config file
    - Implement extract_symptoms() using LangExtract
    - Implement extract_medications() using LangExtract
    - Implement extract_diagnoses() using LangExtract
    - _Requirements: 3.1, 3.2, 3.3, 13.2, 14.1_

  - [ ] 7.2 Implement remaining extraction methods
    - Implement extract_vital_signs()
    - Implement extract_physical_exam()
    - Implement extract_red_flags()
    - Implement extract_follow_up()
    - Implement extract_all() to orchestrate all extractions
    - _Requirements: 3.4, 3.5, 3.6, 3.7, 13.2, 14.1_

  - [ ] 7.3 Add retry logic and error handling
    - Implement exponential backoff for API failures
    - Handle rate limits with wait and retry
    - Log extraction errors with context
    - _Requirements: 2.5, 9.3, 14.1_

  - [ ] 7.4 Write unit tests for ClinicalEntityExtractor
    - Mock LangExtract API calls
    - Test each extraction method with sample text
    - Test error handling and retry logic
    - Test relationship attribute grouping
    - _Requirements: 3.8, 3.9, 14.1_

- [ ] 8. Implement data validation
  - [ ] 8.1 Create Validator class in validator.py
    - Implement validate_severity() for allowed values
    - Implement validate_certainty() for diagnostic certainty
    - Implement validate_dosage() for positive numbers
    - Implement validate_date() for ISO 8601 format
    - Implement validate_all() to run all validations
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 14.1_

  - [ ] 8.2 Add validation logging
    - Log warnings for validation failures
    - Continue processing after validation failures
    - Track validation statistics
    - _Requirements: 11.5, 14.1_

  - [ ] 8.3 Write unit tests for Validator
    - Test each validation rule
    - Test validation error messages
    - Test validate_all() aggregation
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 14.1_

- [ ] 9. Implement database schema mapping
  - [ ] 9.1 Create DataMapper class in data_mapper.py
    - Initialize with consultation_session_id, patient_id, doctor_id
    - Implement UUID generation for all primary keys
    - Implement timestamp generation in UTC
    - _Requirements: 5.2, 5.3, 13.4, 14.1_

  - [ ] 9.2 Implement symptom mapping
    - Create map_symptoms() to convert to SYMPTOMS table format
    - Handle symptom_group attribute for relationship linking
    - Map severity, duration, onset, temporal_pattern
    - Generate confidence scores
    - _Requirements: 3.1, 5.1, 13.4, 14.1_

  - [ ] 9.3 Implement medication mapping
    - Create map_medications() to convert to MEDICATIONS table format
    - Handle medication_group attribute for grouping
    - Map dosage, route, frequency, duration, indication
    - _Requirements: 3.2, 5.1, 13.4, 14.1_

  - [ ] 9.4 Implement diagnosis and assessment mapping
    - Create map_diagnoses() for DIAGNOSES table
    - Create mapping for CLINICAL_ASSESSMENT_EXTRACTED table
    - Handle diagnostic certainty and reasoning
    - Map key clinical features
    - _Requirements: 3.3, 5.1, 13.4, 14.1_

  - [ ] 9.5 Implement vital signs and physical exam mapping
    - Create map_vital_signs() for VITAL_SIGNS table
    - Create map_physical_exam() for PHYSICAL_EXAMINATION_FINDINGS table
    - Handle measurement units and reference ranges
    - _Requirements: 3.4, 3.5, 5.1, 13.4, 14.1_

  - [ ] 9.6 Implement red flags and follow-up mapping
    - Create map_red_flags() for RED_FLAGS_AND_WARNINGS table
    - Create map_follow_up() for FOLLOW_UP_PLAN_EXTRACTED table
    - Map severity and priority levels
    - _Requirements: 3.6, 3.7, 5.1, 13.4, 14.1_

  - [ ] 9.7 Implement consultation session mapping
    - Create generate_consultation_session() for CONSULTATION_SESSIONS table
    - Create generate_consultation() for CONSULTATIONS table
    - Include full transcript and metadata
    - Set nlp_processed_flag appropriately
    - _Requirements: 5.1, 5.4, 13.4, 14.1_

  - [ ] 9.8 Handle empty tables
    - Generate empty DataFrames with headers for tables with no data
    - Maintain schema consistency
    - _Requirements: 5.5, 13.4, 14.1_

  - [ ] 9.9 Write unit tests for DataMapper
    - Test UUID generation and consistency
    - Test each mapping method with sample data
    - Test foreign key relationships
    - Test empty table handling
    - _Requirements: 5.2, 5.3, 5.4, 14.1_

- [ ] 10. Implement CSV export
  - [ ] 10.1 Create CSVExporter class in csv_exporter.py
    - Initialize with output directory
    - Implement export_table() for single DataFrame
    - Handle CSV encoding (UTF-8)
    - Handle NULL values as empty strings
    - Escape special characters properly
    - _Requirements: 7.2, 7.3, 7.4, 14.1_

  - [ ] 10.2 Implement JSONB serialization
    - Serialize JSONB fields as JSON strings
    - Ensure valid JSON format
    - _Requirements: 7.5, 14.1_

  - [ ] 10.3 Implement batch export
    - Create export_all() to export all tables
    - Return list of generated file paths
    - _Requirements: 7.1, 14.1_

  - [ ] 10.4 Implement manifest generation
    - Create create_manifest() to generate manifest file
    - Include extraction timestamp, consultation_session_id
    - List all generated files with row counts
    - Include total entities extracted and processing time
    - _Requirements: 7.6, 14.1_

  - [ ] 10.5 Write unit tests for CSVExporter
    - Test CSV file generation
    - Test JSONB serialization
    - Test manifest creation
    - Test special character escaping
    - _Requirements: 7.3, 7.5, 14.1_

- [ ] 11. Implement main application orchestration
  - [ ] 11.1 Create main.py entry point
    - Parse command-line arguments (--input, --use-test-data)
    - Initialize ConfigManager
    - Initialize LLMProviderManager and validate credentials
    - Set up logging with structured output
    - _Requirements: 2.4, 9.1, 10.1, 10.2, 10.3, 13.1, 13.5, 14.1_

  - [ ] 11.2 Implement extraction pipeline
    - Read input file using InputHandler
    - Generate or load patient/doctor data based on --use-test-data flag
    - Extract entities using ClinicalEntityExtractor
    - Validate extracted data using Validator
    - Map entities to database schema using DataMapper
    - Export CSVs using CSVExporter
    - _Requirements: 1.1, 3.8, 6.1, 6.5, 13.1, 13.2, 14.1_

  - [ ] 11.3 Add comprehensive error handling
    - Handle input errors (file not found, invalid format)
    - Handle configuration errors (missing credentials)
    - Handle extraction errors (API failures, low confidence)
    - Handle validation errors (invalid data values)
    - Handle export errors (file write failures)
    - Return appropriate exit codes
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 14.1_

  - [ ] 11.4 Implement logging and monitoring
    - Log processing start and completion
    - Log extraction progress for each entity type
    - Log validation warnings
    - Log summary statistics (entities extracted, processing time)
    - Use structured JSON logging format
    - _Requirements: 9.1, 9.2, 9.4, 12.4, 14.1_

  - [ ] 11.5 Add performance optimizations
    - Implement LangExtract chunking for long transcripts
    - Stream CSV writes to avoid memory issues
    - Cache few-shot examples
    - _Requirements: 12.1, 12.3, 14.1_

- [ ] 12. Create Docker configuration
  - [ ] 12.1 Create Dockerfile
    - Use Python 3.12-slim base image
    - Install dependencies from requirements.txt
    - Copy application code
    - Create output directory
    - Set environment variables
    - Define entry point
    - _Requirements: 8.1, 8.5, 13.5, 14.1_

  - [ ] 12.2 Create docker-compose.yml
    - Define extractor service
    - Configure volume mounts for input and output
    - Set environment variables
    - Define command with --use-test-data flag
    - _Requirements: 8.2, 8.3, 8.4, 13.5, 14.1_

  - [ ] 12.3 Create .dockerignore
    - Exclude unnecessary files from Docker build
    - _Requirements: 8.1, 14.1_

- [ ] 13. Write integration tests
  - [ ] 13.1 Create test_integration.py
    - Test end-to-end extraction with case_1.md
    - Test end-to-end extraction with case_2.md
    - Verify CSV outputs match expected schema
    - Verify manifest file is generated correctly
    - _Requirements: 1.4, 14.1_

  - [ ] 13.2 Test error scenarios
    - Test empty consultation (no entities)
    - Test malformed input handling
    - Test API failure and retry
    - _Requirements: 9.2, 9.3, 14.1_

  - [ ] 13.3 Test with --use-test-data flag
    - Verify test data generation
    - Verify UUIDs are consistent
    - _Requirements: 6.1, 6.4, 14.1_

- [ ] 14. Create project documentation
  - [ ] 14.1 Create main README.md
    - Project overview and features
    - Installation instructions
    - Usage examples (with and without Docker)
    - Configuration guide
    - Environment variables reference
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 14.1_

  - [ ] 14.2 Create src/README.md
    - Module documentation
    - Component responsibilities
    - Usage examples for each class
    - _Requirements: 1.1, 14.1_

  - [ ] 14.3 Create tests/README.md
    - Testing strategy
    - How to run tests
    - Test data requirements
    - _Requirements: 1.4, 14.1_

  - [ ] 14.4 Create config/README.md
    - Configuration options
    - Environment variables
    - Few-shot example format
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.1, 10.2, 10.3, 14.1_

  - [ ] 14.5 Create input/README.md
    - Input file format specification
    - Validation rules
    - Example consultation format
    - _Requirements: 1.1, 1.2, 14.1_

  - [ ] 14.6 Create output/README.md
    - Output CSV format
    - Manifest structure
    - Database ingestion guide
    - _Requirements: 7.1, 7.2, 7.6, 14.1_

  - [ ] 14.7 Create docs/architecture.md
    - Mermaid diagram of complete database schema
    - Table relationships and foreign keys
    - Cardinality notation
    - _Requirements: 5.1, 14.1_

- [ ] 15. Final testing and validation
  - [ ] 15.1 Run full test suite
    - Execute all unit tests
    - Execute all integration tests
    - Verify test coverage
    - _Requirements: 1.4, 14.1_

  - [ ] 15.2 Test Docker build and run
    - Build Docker image
    - Run container with sample consultation
    - Verify CSV outputs
    - Test with both Gemini and Bedrock (if credentials available)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 13.5, 14.1_

  - [ ] 15.3 Validate against requirements
    - Verify all 14 requirements are met
    - Test performance targets (<60s for typical consultation)
    - Verify exit codes
    - _Requirements: 12.4, 8.5, 14.1_

  - [ ] 15.4 Create final commit
    - Commit all changes with comprehensive message
    - Tag release version
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
