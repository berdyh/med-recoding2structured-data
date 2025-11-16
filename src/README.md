# Source Code Documentation

This directory contains the core application modules for the GP Consultation Data Extraction System.

## Module Overview

### Core Modules

#### `main.py`
**Entry point** for the application.

**Responsibilities:**
- Parse command-line arguments
- Initialize all components
- Orchestrate the extraction pipeline
- Handle errors and logging
- Return appropriate exit codes

**Usage:**
```python
# Run from command line
python -m src.main --input input/case_1.md --use-test-data
```

#### `config_manager.py`
**Configuration management** with environment variable support.

**Responsibilities:**
- Load configuration from YAML file
- Override with environment variables
- Validate required configuration
- Provide configuration access to other modules

**Usage:**
```python
from config_manager import ConfigManager

config = ConfigManager('config/config.yaml')
api_key = config.get('llm.gemini.api_key')
```

#### `llm_provider.py`
**LLM provider abstraction** for Gemini and AWS Bedrock.

**Responsibilities:**
- Select LLM provider based on configuration
- Validate API credentials
- Provide unified interface for LLM access
- Handle AWS Bedrock boto3 client

**Usage:**
```python
from llm_provider import LLMProviderManager

llm_provider = LLMProviderManager(config)
provider_name = llm_provider.get_provider()  # 'gemini' or 'bedrock'
credentials = llm_provider.get_api_credentials()
```

### Input/Output Modules

#### `input_handler.py`
**Input file reading and validation**.

**Responsibilities:**
- Read Markdown consultation files
- Validate file format
- Handle encoding errors
- Provide transcript text to extractor

**Usage:**
```python
from input_handler import InputHandler

handler = InputHandler()
transcript = handler.read_transcript('input/case_1.md')
is_valid = handler.validate_format(transcript)
```

#### `csv_exporter.py`
**CSV file generation** for database ingestion.

**Responsibilities:**
- Export DataFrames to CSV files
- Serialize JSONB columns
- Handle special characters and encoding
- Generate manifest file

**Usage:**
```python
from csv_exporter import CSVExporter

exporter = CSVExporter('output')
file_paths = exporter.export_all(mapped_data)
manifest = exporter.create_manifest(session_id, total_entities, processing_time)
```

### Extraction Modules

#### `entity_extractor.py`
**Clinical entity extraction** using LangExtract.

**Responsibilities:**
- Load few-shot examples from configuration
- Extract symptoms, medications, diagnoses, etc.
- Handle API retries and errors
- Group related entities using attributes

**Usage:**
```python
from entity_extractor import ClinicalEntityExtractor

extractor = ClinicalEntityExtractor(llm_provider)
entities = extractor.extract_all(transcript)

# Extract specific entity types
symptoms = extractor.extract_symptoms(transcript)
medications = extractor.extract_medications(transcript)
```

**Entity Types:**
- `symptoms`: Patient-reported symptoms with severity and duration
- `medications`: Prescribed medications with dosage and frequency
- `diagnoses`: Diagnostic conclusions with certainty
- `vital_signs`: Clinical measurements (BP, temperature, etc.)
- `physical_exam`: Physical examination findings
- `red_flags`: Warning signs requiring attention
- `follow_up`: Follow-up instructions and timing

### Data Processing Modules

#### `data_mapper.py`
**Database schema mapping** for extracted entities.

**Responsibilities:**
- Map extracted entities to database tables
- Generate UUIDs for primary keys
- Handle foreign key relationships
- Parse and normalize extracted values
- Generate empty DataFrames for tables with no data

**Usage:**
```python
from data_mapper import DataMapper
import uuid

mapper = DataMapper(
    consultation_session_id=uuid.uuid4(),
    patient_id=uuid.uuid4(),
    doctor_id=uuid.uuid4()
)

# Map entities to tables
symptoms_df = mapper.map_symptoms(extracted_entities['symptoms'])
medications_df = mapper.map_medications(extracted_entities['medications'])
diagnoses_df, assessment_df = mapper.map_diagnoses(extracted_entities['diagnoses'])
```

**Mapping Methods:**
- `map_symptoms()`: Maps to SYMPTOMS table
- `map_medications()`: Maps to MEDICATIONS table
- `map_diagnoses()`: Maps to DIAGNOSES and CLINICAL_ASSESSMENT_EXTRACTED tables
- `map_vital_signs()`: Maps to VITAL_SIGNS table
- `map_physical_exam()`: Maps to PHYSICAL_EXAMINATION_FINDINGS table
- `map_red_flags()`: Maps to RED_FLAGS_AND_WARNINGS table
- `map_follow_up()`: Maps to FOLLOW_UP_PLAN_EXTRACTED table
- `generate_consultation_session()`: Creates CONSULTATION_SESSIONS row
- `generate_consultation()`: Creates CONSULTATIONS row

#### `validator.py`
**Data validation** against business rules.

**Responsibilities:**
- Validate severity values
- Validate diagnostic certainty
- Validate dosages and measurements
- Validate dates and timestamps
- Log validation warnings (non-blocking)

**Usage:**
```python
from validator import Validator

validator = Validator()
is_valid, errors = validator.validate_all(extracted_entities)

# Validate specific fields
is_valid_severity = validator.validate_severity('moderate')
is_valid_certainty = validator.validate_certainty('probable')
is_valid_dosage = validator.validate_dosage(100.0)
```

**Validation Rules:**
- Severity: `mild`, `moderate`, `severe`, `critical`
- Certainty: `confirmed`, `probable`, `suspected`, `ruled_out`
- Dosages: Must be positive numbers
- Dates: ISO 8601 format, not in future
- NHS numbers: 10 digits with valid checksum

### Utility Modules

#### `test_data_generator.py`
**Test data generation** for patients and doctors.

**Responsibilities:**
- Generate realistic UK patient data
- Generate doctor data with specialties
- Generate valid NHS numbers with checksum
- Ensure consistent UUIDs

**Usage:**
```python
from test_data_generator import TestDataGenerator

generator = TestDataGenerator()
patient = generator.generate_patient()
doctor = generator.generate_doctor()

print(patient['nhs_number'])  # Valid NHS number
print(patient['patient_id'])  # UUID
```

**Generated Fields:**
- Patient: name, NHS number, date of birth, gender, address, phone, email
- Doctor: name, GMC number, specialty, contact information

## Data Flow

```
1. main.py
   ↓
2. input_handler.py → Read transcript
   ↓
3. entity_extractor.py → Extract entities using LLM
   ↓
4. validator.py → Validate extracted data
   ↓
5. data_mapper.py → Map to database schema
   ↓
6. csv_exporter.py → Export CSV files
```

## Error Handling

All modules use custom exception classes:

- `ConfigurationError`: Configuration issues
- `LLMProviderError`: LLM provider issues
- `ExtractionError`: Entity extraction failures
- `ValidationError`: Data validation failures

Errors are logged with context and appropriate exit codes are returned.

## Logging

All modules use Python's `logging` module:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing started")
logger.warning("Validation warning: invalid severity")
logger.error("Extraction failed", exc_info=True)
```

Log levels:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (non-blocking)
- `ERROR`: Error messages (may block processing)

## Testing

Each module has corresponding unit tests in `tests/`:

- `test_config_manager.py`
- `test_llm_provider.py`
- `test_input_handler.py`
- `test_entity_extractor.py`
- `test_data_mapper.py`
- `test_validator.py`
- `test_csv_exporter.py`
- `test_test_data_generator.py`

Run tests:
```bash
pytest tests/test_<module_name>.py
```

## Dependencies

Key dependencies:
- `langextract`: Clinical entity extraction
- `pandas`: Data manipulation and CSV export
- `pyyaml`: Configuration file parsing
- `boto3`: AWS Bedrock client (optional)
- `google-generativeai`: Gemini client (optional)

See `requirements.txt` for complete list.

## Development Guidelines

1. **Type Hints**: Use type hints for all function parameters and return values
2. **Docstrings**: Document all classes and methods with docstrings
3. **Error Handling**: Use try-except blocks with specific exception types
4. **Logging**: Log important events and errors with appropriate levels
5. **Testing**: Write unit tests for all new functionality
6. **Code Style**: Follow PEP 8 style guidelines

## Module Dependencies

```
main.py
├── config_manager.py
├── llm_provider.py
│   └── config_manager.py
├── input_handler.py
├── entity_extractor.py
│   └── llm_provider.py
├── data_mapper.py
├── validator.py
├── csv_exporter.py
└── test_data_generator.py
```

## Performance Considerations

- **Few-shot examples**: Cached after first load
- **CSV export**: Streamed to avoid memory issues
- **LLM calls**: Retry logic with exponential backoff
- **Validation**: Non-blocking warnings for data quality

## Future Enhancements

- Batch processing for multiple consultations
- Direct database integration (PostgreSQL)
- Real-time processing for live consultations
- Multi-language support
- Active learning for few-shot examples
