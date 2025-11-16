# Requirements Document

## Introduction

This system extracts structured clinical data from unstructured GP consultation transcripts (Markdown format) using the LangExtract library with LLM-powered NLP. The extracted data is mapped to a PostgreSQL database schema and exported as multiple CSV files for database ingestion. The system is containerized with Docker for portability and includes test data generation capabilities.

## Requirements

### Requirement 1: Input Processing

**User Story:** As a healthcare data analyst, I want to process GP consultation transcripts in Markdown format, so that I can extract structured clinical information for database storage.

#### Acceptance Criteria

1. WHEN a Markdown file is provided as input THEN the system SHALL read and parse the file content
2. WHEN the file contains consultation transcript THEN the system SHALL extract the full text for NLP processing
3. IF the file is not found or unreadable THEN the system SHALL raise a clear error message
4. WHEN processing multiple files THEN the system SHALL handle each file independently

### Requirement 2: LangExtract Integration with Multiple LLM Providers

**User Story:** As a system administrator, I want to configure different LLM providers (Gemini or Claude via AWS Bedrock), so that I can choose the most suitable model for extraction.

#### Acceptance Criteria

1. WHEN LANGEXTRACT_API_KEY environment variable is set THEN the system SHALL use it for Gemini API authentication
2. WHEN AWS_BEDROCK configuration is provided THEN the system SHALL use Claude Sonnet 4.5 via AWS Bedrock
3. WHEN using AWS Bedrock THEN the system SHALL use model ID `anthropic.claude-sonnet-4-5-20250929-v1:0`
4. IF no valid API credentials are found THEN the system SHALL raise a configuration error
5. WHEN extraction fails THEN the system SHALL log the error with model details and retry once

### Requirement 3: Clinical Entity Extraction

**User Story:** As a clinical data engineer, I want to extract symptoms, medications, diagnoses, and other clinical entities from consultation transcripts, so that I can populate the database tables accurately.

#### Acceptance Criteria

1. WHEN processing a transcript THEN the system SHALL extract symptoms with attributes (name, severity, duration, onset, temporal pattern)
2. WHEN medications are mentioned THEN the system SHALL extract medication name, dosage, route, frequency, duration, and indication
3. WHEN diagnoses are stated THEN the system SHALL extract diagnosis name, certainty level, and supporting clinical features
4. WHEN vital signs are recorded THEN the system SHALL extract temperature, blood pressure, heart rate, oxygen saturation, and respiratory rate
5. WHEN physical examination findings are described THEN the system SHALL extract examination type, anatomical site, findings, and severity
6. WHEN red flags or warnings are mentioned THEN the system SHALL extract warning description, type, and severity
7. WHEN follow-up plans are discussed THEN the system SHALL extract follow-up type, timing, condition, action, and priority
8. IF an entity type is not present in the transcript THEN the system SHALL leave corresponding table data empty
9. WHEN extracting entities THEN the system SHALL use relationship attributes to link related information (e.g., medication_group)

### Requirement 4: Few-Shot Learning Configuration

**User Story:** As an NLP engineer, I want to define extraction examples for LangExtract, so that the model learns the correct extraction patterns for medical entities.

#### Acceptance Criteria

1. WHEN configuring extraction THEN the system SHALL provide few-shot examples for each entity type
2. WHEN defining examples THEN each example SHALL include extraction_class, extraction_text, and attributes
3. WHEN extracting medications THEN examples SHALL demonstrate medication grouping using medication_group attribute
4. WHEN extracting symptoms THEN examples SHALL demonstrate severity, duration, and temporal pattern extraction
5. WHEN extracting diagnoses THEN examples SHALL demonstrate certainty levels and clinical reasoning

### Requirement 5: Database Schema Mapping

**User Story:** As a database administrator, I want extracted data mapped to the PostgreSQL schema defined in full_db_plan.md, so that data can be ingested into the database correctly.

#### Acceptance Criteria

1. WHEN extraction completes THEN the system SHALL map entities to these MVP tables:
   - CONSULTATION_SESSIONS
   - CONSULTATIONS
   - SYMPTOMS
   - MEDICATIONS
   - ASSOCIATED_FINDINGS
   - PHYSICAL_EXAMINATION_FINDINGS
   - REVIEW_OF_SYSTEMS
   - VITAL_SIGNS
   - LABORATORY_RESULTS
   - CLINICAL_ASSESSMENT_EXTRACTED
   - RED_FLAGS_AND_WARNINGS
   - FOLLOW_UP_PLAN_EXTRACTED
   - ALLERGIES
   - DIAGNOSES
   - SEVERITY_LEVELS (lookup table)
   - DIAGNOSTIC_CERTAINTY (lookup table)
2. WHEN generating UUIDs THEN the system SHALL use uuid4() for all primary keys
3. WHEN generating timestamps THEN the system SHALL use current UTC time
4. WHEN mapping relationships THEN the system SHALL maintain foreign key integrity
5. IF a table has no data THEN the system SHALL create an empty CSV with headers only

### Requirement 6: Test Data Generation

**User Story:** As a developer, I want to generate sample patient and doctor data with one click, so that I can test the system without manual data entry.

#### Acceptance Criteria

1. WHEN --use-test-data flag is provided THEN the system SHALL generate sample patient data automatically
2. WHEN generating test data THEN the system SHALL create realistic NHS numbers, names, and contact information
3. WHEN generating test data THEN the system SHALL create sample doctor profiles with specialties
4. WHEN generating test data THEN the system SHALL use consistent UUIDs across related records
5. WHEN --use-test-data is not provided THEN the system SHALL prompt for patient_id and doctor_id or generate them from metadata

### Requirement 7: CSV Export

**User Story:** As a data engineer, I want extracted data exported as multiple CSV files (one per table), so that I can ingest them into PostgreSQL efficiently.

#### Acceptance Criteria

1. WHEN extraction completes THEN the system SHALL generate one CSV file per database table
2. WHEN creating CSV files THEN each file SHALL include column headers matching the database schema
3. WHEN writing CSV data THEN the system SHALL properly escape special characters and handle NULL values
4. WHEN writing timestamps THEN the system SHALL use ISO 8601 format
5. WHEN writing JSONB fields THEN the system SHALL serialize as valid JSON strings
6. WHEN all CSVs are generated THEN the system SHALL create a manifest file listing all output files

### Requirement 8: Docker Containerization

**User Story:** As a DevOps engineer, I want the system containerized with Docker, so that it can run consistently across different environments.

#### Acceptance Criteria

1. WHEN building the Docker image THEN it SHALL include Python 3.12+ (ideally 3.14), langextract, and all dependencies
2. WHEN running the container THEN it SHALL accept input file path as a volume mount
3. WHEN running the container THEN it SHALL accept environment variables for API keys
4. WHEN running the container THEN it SHALL output CSV files to a mounted output directory
5. WHEN the container exits THEN it SHALL return appropriate exit codes (0 for success, non-zero for errors)

### Requirement 9: Error Handling and Logging

**User Story:** As a system operator, I want comprehensive error handling and logging, so that I can troubleshoot issues quickly.

#### Acceptance Criteria

1. WHEN an error occurs THEN the system SHALL log the error with timestamp, severity, and context
2. WHEN extraction fails THEN the system SHALL log which entities failed and why
3. WHEN API rate limits are hit THEN the system SHALL implement exponential backoff retry
4. WHEN processing completes THEN the system SHALL log summary statistics (entities extracted, tables populated, processing time)
5. WHEN running in verbose mode THEN the system SHALL log detailed extraction progress

### Requirement 10: Configuration Management

**User Story:** As a system administrator, I want to configure extraction parameters via environment variables and config files, so that I can customize behavior without code changes.

#### Acceptance Criteria

1. WHEN LANGEXTRACT_API_KEY is set THEN the system SHALL use Gemini API
2. WHEN AWS_BEDROCK_ENABLED=true THEN the system SHALL use Claude via AWS Bedrock
3. WHEN AWS_REGION is set THEN the system SHALL use that region for Bedrock
4. WHEN MODEL_ID is set THEN the system SHALL override the default model
5. WHEN EXTRACTION_CONFIDENCE_THRESHOLD is set THEN the system SHALL filter low-confidence extractions

### Requirement 11: Extraction Validation

**User Story:** As a quality assurance analyst, I want extracted data validated against business rules, so that only valid data is exported.

#### Acceptance Criteria

1. WHEN extracting severity THEN the system SHALL validate against allowed values (mild, moderate, severe, critical)
2. WHEN extracting diagnostic certainty THEN the system SHALL validate against allowed values (confirmed, probable, suspected, ruled_out)
3. WHEN extracting dates THEN the system SHALL validate date formats and logical consistency
4. WHEN extracting dosages THEN the system SHALL validate numeric values are positive
5. WHEN validation fails THEN the system SHALL log warnings but continue processing

### Requirement 12: Performance Optimization

**User Story:** As a system architect, I want the system to process consultations efficiently, so that it can scale to handle large volumes.

#### Acceptance Criteria

1. WHEN processing long transcripts THEN the system SHALL use LangExtract's chunking strategy
2. WHEN extracting multiple entity types THEN the system SHALL batch API calls where possible
3. WHEN generating CSVs THEN the system SHALL stream data to avoid memory issues
4. WHEN processing completes THEN the system SHALL report total processing time and tokens used
5. WHEN running in production THEN the system SHALL process a typical consultation in under 60 seconds

### Requirement 13: Development Tooling and Information Access

**User Story:** As a developer, I want to leverage MCP (Model Context Protocol) servers during development, so that I can access accurate, up-to-date information and improve code quality.

#### Acceptance Criteria

1. WHEN developing the system THEN the developer SHALL use available MCP servers to access current documentation
2. WHEN implementing LangExtract integration THEN the developer SHALL use MCP tools or URL search to verify API specifications and best practices
3. WHEN implementing AWS Bedrock integration THEN the developer SHALL use AWS documentation MCP server for accurate configuration
4. WHEN writing database schema code THEN the developer SHALL use MCP tools or URL search to verify PostgreSQL syntax and data types
5. WHEN implementing Docker configuration THEN the developer SHALL use MCP tools to access current Docker best practices

### Requirement 14: Version Control and Incremental Commits

**User Story:** As a developer, I want to commit small, incremental changes to version control after completing each task, so that I can maintain a clear development history and easily revert changes if needed.

#### Acceptance Criteria

1. WHEN completing a task or sub-task THEN the developer SHALL commit the changes to version control
2. WHEN making a commit THEN the commit message SHALL clearly describe what was implemented
3. WHEN making a commit THEN the commit message SHALL reference the task number from the implementation plan
4. WHEN a task involves multiple logical changes THEN the developer SHALL make separate commits for each logical unit
5. WHEN all changes for a task are committed THEN the developer SHALL verify the code is in a working state and push changes into the remote branch #[u2s-implementation] before proceeding to the next task
