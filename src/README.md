# Source Code Modules

This directory contains the core application modules for the GP Consultation Data Extraction System.

## Module Overview

### Core Components

#### `main.py`
**Purpose**: Application entry point and orchestration

**Responsibilities**:
- Parse command-line arguments
- Initialize all components
- Orchestrate the extraction pipeline
- Handle errors and logging
- Generate summary statistics

**Usage**:
```python
python -m src.main --input input/consultation.md --use-test-data
```

#### `input_handler.py`
**Purpose**: Read and validate input consultation transcripts

**Responsibilities**:
- Read Markdown files with UTF-8 encoding
- Validate input format
- Handle file not found and encoding errors

**Usage**:
```python
from src.input_handler import InputHandler

handler = InputHandler()
transcript = handler.read_transcript("input/consultation.md")
is_valid = handler.validate_format(transcript)
```

#### `llm_provider.py`
**Purpose**: Manage LLM provider connections (Gemini or AWS Bedrock)

**Responsibilities**:
- Select active LLM provider based on configuration
- Validate API credentials
- Provide provider-specific configuration

**Usage**:
```python
from src.llm_provider import LLMProviderManager

provider_manager = LLMProviderManager(config)
provider = provider_manager.get_provider()  # "gemini" or "bedrock"
credentials = provider_manager.get_api_credentials()
```

#### `entity_extractor.py`
**Purpose**: Extract clinical entities using LangExtract

**Responsibilities**:
- Initialize LangExtract with few-shot examples
- Extract symptoms, medications, diagnoses, vital signs, etc.
- Handle API failures with retry logic
- Return structured entity data

**Usage**:
```python
from src.entity_extractor import ClinicalEntityExtractor

extractor = ClinicalEntityExtractor(llm_provider_manager)
entities = extractor.extract_all(transcript)
# Returns: {"symptoms": [...], "medications": [...], ...}
```

#### `data_mapper.py`
**Purpose**: Map extracted entities to database schema

**Responsibilities**:
- Generate UUIDs for all primary keys
- Map entities to database table format
- Maintain foreign key relationships
- Handle empty tables

**Usage**:
```python
from src.data_mapper import DataMapper

mapper = DataMapper(consultation_session_id, patient_id, doctor_id)
symptoms_df = mapper.map_symptoms(entities["symptoms"])
medications_df = mapper.map_medications(entities["medications"])
```

#### `csv_exporter.py`
**Purpose**: Export data as CSV files

**Responsibilities**:
- Generate CSV files for each table
- Handle JSONB serialization
- Create manifest file
- Proper character escaping

**Usage**:
```python
from src.csv_exporter import CSVExporter

exporter = CSVExporter(output_dir="output")
file_paths = exporter.export_all(mapped_data)
manifest_path = exporter.create_manifest(file_paths)
```

#### `test_data_generator.py`
**Purpose**: Generate realistic test data

**Responsibilities**:
- Generate sample patient data with valid NHS numbers
- Generate sample doctor profiles
- Ensure consistent UUIDs across relationships

**Usage**:
```python
from src.test_data_generator import TestDataGenerator

generator = TestDataGenerator()
patient = generator.generate_patient()
doctor = generator.generate_doctor()
```

#### `config_manager.py`
**Purpose**: Manage application configuration

**Responsibilities**:
- Load configuration from YAML and environment variables
- Validate required parameters
- Provide configuration access

**Usage**:
```python
from src.config_manager import ConfigManager

config = ConfigManager("config/config.yaml")
api_key = config.get("llm.gemini.api_key")
```

#### `validator.py`
**Purpose**: Validate extracted data

**Responsibilities**:
- Validate severity levels
- Validate diagnostic certainty
- Validate dates and dosages
- Log validation warnings

**Usage**:
```python
from src.validator import Validator

validator = Validator()
is_valid, errors = validator.validate_all(extracted_data)
```

## Component Interaction Flow

```
main.py
  ↓
input_handler.py → Read transcript
  ↓
config_manager.py → Load configuration
  ↓
llm_provider.py → Initialize LLM provider
  ↓
entity_extractor.py → Extract entities
  ↓
validator.py → Validate data
  ↓
data_mapper.py → Map to database schema
  ↓
csv_exporter.py → Export CSV files
```

## Error Handling

All modules raise specific exceptions:
- `ConfigurationError`: Configuration issues
- `LLMProviderError`: LLM provider failures
- `ValidationError`: Data validation failures
- `ExtractionError`: General extraction errors

## Logging

All modules use structured JSON logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.info({"event": "extraction_complete", "entities": 42})
```

## Development Guidelines

1. Each module should be self-contained with clear responsibilities
2. Use type hints for all function signatures
3. Include docstrings for all public methods
4. Handle errors gracefully with appropriate exceptions
5. Log important events and errors
6. Write unit tests for all public methods
