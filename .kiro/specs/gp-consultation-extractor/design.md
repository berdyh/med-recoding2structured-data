# Design Document

## Overview

The GP Consultation Data Extraction System is a Python-based application that processes unstructured GP consultation transcripts in Markdown format and extracts structured clinical data using LangExtract with LLM-powered NLP. The system maps extracted entities to a PostgreSQL database schema and exports data as CSV files for database ingestion.

### Key Design Principles

1. **Separation of Concerns**: Clear boundaries between extraction, mapping, and export layers
2. **Extensibility**: Support for multiple LLM providers (Gemini, AWS Bedrock Claude)
3. **Data Integrity**: Maintain foreign key relationships and UUID consistency across tables
4. **Error Resilience**: Comprehensive error handling with retry logic and detailed logging
5. **Containerization**: Docker-first approach for consistent deployment
6. **Incremental Development**: Small, testable commits after each task completion for clear development history
7. **Documentation-Driven**: Leverage MCP servers and current documentation for accurate implementation

### Technology Stack

- **Language**: Python 3.12+ (ideally 3.14 for latest features)
- **NLP Library**: LangExtract (with Gemini 2.5 Pro or Claude Sonnet 4.5 via AWS Bedrock)
- **Data Processing**: Pandas for CSV generation
- **Containerization**: Docker with multi-stage builds
- **Configuration**: Environment variables and YAML config files
- **Logging**: Python logging module with structured output
- **Version Control**: Git for incremental commits after each task completion

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Main Application                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  1. Input Handler                               │  │  │
│  │  │     - Read Markdown files                       │  │  │
│  │  │     - Validate input format                     │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                        ↓                              │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  2. LLM Provider Manager                        │  │  │
│  │  │     - Gemini API client                         │  │  │
│  │  │     - AWS Bedrock client                        │  │  │
│  │  │     - Provider selection logic                  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                        ↓                              │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  3. Clinical Entity Extractor                   │  │  │
│  │  │     - LangExtract integration                   │  │  │
│  │  │     - Few-shot learning configuration           │  │  │
│  │  │     - Entity extraction orchestration           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                        ↓                              │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  4. Data Mapper                                 │  │  │
│  │  │     - Entity → Database schema mapping          │  │  │
│  │  │     - UUID generation and relationship linking  │  │  │
│  │  │     - Data validation                           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                        ↓                              │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  5. CSV Exporter                                │  │  │
│  │  │     - Generate CSV files per table              │  │  │
│  │  │     - Handle JSONB serialization                │  │  │
│  │  │     - Create manifest file                      │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Supporting Components                                │  │
│  │  - Configuration Manager                             │  │
│  │  - Logger                                            │  │
│  │  - Test Data Generator                               │  │
│  │  - Validation Engine                                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ↑ Input                              ↓ Output
    [Markdown Files]                    [CSV Files + Manifest]
```

### Data Flow

1. **Input Phase**: Read Markdown consultation transcript
2. **Extraction Phase**: Use LangExtract with configured LLM to extract clinical entities
3. **Mapping Phase**: Transform extracted entities into database schema format
4. **Export Phase**: Generate CSV files for each database table
5. **Validation Phase**: Verify data integrity and log summary statistics

---

## Components and Interfaces

### 1. Input Handler (`input_handler.py`)

**Responsibility**: Read and validate Markdown input files

**Interface**:
```python
class InputHandler:
    def read_transcript(self, file_path: str) -> str:
        """Read Markdown file and return content"""
        
    def validate_format(self, content: str) -> bool:
        """Validate that content is properly formatted"""
```

**Key Methods**:
- `read_transcript()`: Reads file with UTF-8 encoding, handles file not found errors
- `validate_format()`: Checks for minimum required structure (patient/GP dialogue)

---

### 2. LLM Provider Manager (`llm_provider.py`)

**Responsibility**: Manage connections to different LLM providers

**Interface**:
```python
class LLMProviderManager:
    def __init__(self, config: dict):
        """Initialize with configuration"""
        
    def get_provider(self) -> str:
        """Return active provider name (gemini or bedrock)"""
        
    def get_api_credentials(self) -> dict:
        """Return credentials for active provider"""
        
    def validate_credentials(self) -> bool:
        """Verify credentials are valid"""
```

**Configuration**:
- Environment variables: `LANGEXTRACT_API_KEY`, `AWS_BEDROCK_ENABLED`, `AWS_REGION`, `MODEL_ID`
- Default model for Bedrock: `anthropic.claude-sonnet-4-5-20250929-v1:0`
- Default model for Gemini: `gemini-2.5-pro`

**Design Rationale**: 
- Provider abstraction allows switching between Gemini and AWS Bedrock without code changes
- Environment variable configuration enables different setups for dev/staging/production
- Credential validation at startup prevents runtime failures during extraction
- MCP servers (AWS documentation) should be consulted during implementation for accurate Bedrock configuration

---

### 3. Clinical Entity Extractor (`entity_extractor.py`)

**Responsibility**: Extract structured clinical entities using LangExtract

**Interface**:
```python
class ClinicalEntityExtractor:
    def __init__(self, llm_provider: LLMProviderManager):
        """Initialize with LLM provider"""
        
    def extract_symptoms(self, text: str) -> List[Dict]:
        """Extract symptoms with attributes"""
        
    def extract_medications(self, text: str) -> List[Dict]:
        """Extract medications with grouping"""
        
    def extract_diagnoses(self, text: str) -> List[Dict]:
        """Extract diagnoses with certainty"""
        
    def extract_vital_signs(self, text: str) -> List[Dict]:
        """Extract vital signs measurements"""
        
    def extract_physical_exam(self, text: str) -> List[Dict]:
        """Extract physical examination findings"""
        
    def extract_red_flags(self, text: str) -> List[Dict]:
        """Extract warning signs"""
        
    def extract_follow_up(self, text: str) -> List[Dict]:
        """Extract follow-up plans"""
        
    def extract_all(self, text: str) -> Dict[str, List[Dict]]:
        """Extract all entity types in one pass"""
```

**Few-Shot Examples Configuration**:

Each extraction method uses LangExtract's few-shot learning with examples. The examples follow the relationship extraction pattern demonstrated in the LangExtract documentation, using attributes to group related entities.

**Design Rationale**: Using the `medication_group` attribute (and similar grouping attributes for other entity types) allows the LLM to understand which extracted entities belong together, even when they appear in different parts of the text. This is critical for medical data where a single consultation may mention multiple medications, symptoms, or diagnoses.

```python
# Example for medication extraction
medication_examples = [
    lx.data.ExampleData(
        text="Patient takes Aspirin 100mg daily for heart health.",
        extractions=[
            lx.data.Extraction(
                extraction_class="medication",
                extraction_text="Aspirin",
                attributes={"medication_group": "Aspirin"}  # Group identifier
            ),
            lx.data.Extraction(
                extraction_class="dosage",
                extraction_text="100mg",
                attributes={"medication_group": "Aspirin"}
            ),
            lx.data.Extraction(
                extraction_class="frequency",
                extraction_text="daily",
                attributes={"medication_group": "Aspirin"}
            ),
            lx.data.Extraction(
                extraction_class="indication",
                extraction_text="heart health",
                attributes={"medication_group": "Aspirin"}
            )
        ]
    )
]
```

**Key Implementation Notes**:
- All entities in the order they appear in the text
- Consistent attribute naming across entity types (e.g., `medication_group`, `symptom_group`, `diagnosis_group`)
- Attributes enable post-processing to reconstruct complete clinical records
- Few-shot examples should be stored in `config/few_shot_examples.yaml` for easy modification

**Entity Types and Attributes**:

1. **Symptoms**:
   - Classes: `symptom_name`, `severity`, `duration`, `onset`, `temporal_pattern`
   - Attributes: `symptom_group` (for linking related info)

2. **Medications**:
   - Classes: `medication`, `dosage`, `route`, `frequency`, `duration`, `indication`
   - Attributes: `medication_group` (for grouping related details)

3. **Diagnoses**:
   - Classes: `diagnosis`, `certainty`, `clinical_features`
   - Attributes: `diagnosis_group`

4. **Vital Signs**:
   - Classes: `temperature`, `blood_pressure`, `heart_rate`, `oxygen_saturation`, `respiratory_rate`

5. **Physical Exam**:
   - Classes: `examination_type`, `anatomical_site`, `findings`, `severity`

6. **Red Flags**:
   - Classes: `warning_description`, `warning_type`, `severity`

7. **Follow-up**:
   - Classes: `follow_up_type`, `timing`, `condition`, `action`, `priority`

---

### 4. Data Mapper (`data_mapper.py`)

**Responsibility**: Map extracted entities to database schema

**Interface**:
```python
class DataMapper:
    def __init__(self, consultation_session_id: UUID, patient_id: UUID, doctor_id: UUID):
        """Initialize with core IDs"""
        
    def map_symptoms(self, symptoms: List[Dict]) -> pd.DataFrame:
        """Map symptoms to SYMPTOMS table format"""
        
    def map_medications(self, medications: List[Dict]) -> pd.DataFrame:
        """Map medications to MEDICATIONS table format"""
        
    def map_diagnoses(self, diagnoses: List[Dict]) -> pd.DataFrame:
        """Map diagnoses to DIAGNOSES and CLINICAL_ASSESSMENT_EXTRACTED tables"""
        
    def map_vital_signs(self, vitals: List[Dict]) -> pd.DataFrame:
        """Map vital signs to VITAL_SIGNS table format"""
        
    def map_physical_exam(self, exams: List[Dict]) -> pd.DataFrame:
        """Map physical exam to PHYSICAL_EXAMINATION_FINDINGS table"""
        
    def map_red_flags(self, flags: List[Dict]) -> pd.DataFrame:
        """Map red flags to RED_FLAGS_AND_WARNINGS table"""
        
    def map_follow_up(self, plans: List[Dict]) -> pd.DataFrame:
        """Map follow-up to FOLLOW_UP_PLAN_EXTRACTED table"""
        
    def generate_consultation_session(self, transcript: str, metadata: Dict) -> pd.DataFrame:
        """Generate CONSULTATION_SESSIONS table row"""
        
    def generate_consultation(self, metadata: Dict) -> pd.DataFrame:
        """Generate CONSULTATIONS table row"""
```

**UUID Management**:
- All primary keys use `uuid.uuid4()`
- Foreign keys maintain referential integrity
- Consistent UUIDs across related records

**Timestamp Handling**:
- All timestamps in UTC using `datetime.utcnow()`
- ISO 8601 format for CSV export

---

### 5. CSV Exporter (`csv_exporter.py`)

**Responsibility**: Generate CSV files for database ingestion

**Interface**:
```python
class CSVExporter:
    def __init__(self, output_dir: str):
        """Initialize with output directory"""
        
    def export_table(self, df: pd.DataFrame, table_name: str) -> str:
        """Export DataFrame to CSV file"""
        
    def export_all(self, mapped_data: Dict[str, pd.DataFrame]) -> List[str]:
        """Export all tables and return file paths"""
        
    def create_manifest(self, file_paths: List[str]) -> str:
        """Create manifest file listing all outputs"""
```

**CSV Format**:
- Headers match database column names exactly
- NULL values represented as empty strings
- JSONB fields serialized as JSON strings
- Proper escaping of special characters
- UTF-8 encoding

**Manifest File Format**:
```json
{
  "extraction_timestamp": "2025-11-16T10:30:00Z",
  "consultation_session_id": "uuid-here",
  "files": [
    {
      "table": "CONSULTATION_SESSIONS",
      "file": "consultation_sessions.csv",
      "row_count": 1
    },
    {
      "table": "SYMPTOMS",
      "file": "symptoms.csv",
      "row_count": 5
    }
  ],
  "total_entities_extracted": 42,
  "processing_time_seconds": 15.3
}
```

---

### 6. Test Data Generator (`test_data_generator.py`)

**Responsibility**: Generate realistic test data for patients and doctors with one-click generation

**Interface**:
```python
class TestDataGenerator:
    def generate_patient(self) -> Dict:
        """Generate sample patient data"""
        
    def generate_doctor(self) -> Dict:
        """Generate sample doctor data"""
        
    def generate_nhs_number(self) -> str:
        """Generate valid NHS number with checksum validation"""
```

**Generated Data**:
- Realistic UK names
- Valid NHS numbers (10 digits with checksum)
- UK addresses and phone numbers
- Consistent UUIDs for relationships

**Design Rationale**:
- `--use-test-data` flag enables automatic generation without manual data entry (Requirement 6)
- NHS number generation includes proper checksum validation for realistic test data
- Generated UUIDs are consistent across related records to maintain referential integrity
- When flag is not provided, system prompts for patient_id and doctor_id or generates from metadata

---

### 7. Configuration Manager (`config_manager.py`)

**Responsibility**: Manage application configuration

**Interface**:
```python
class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        """Load configuration from file and environment"""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        
    def validate(self) -> bool:
        """Validate required configuration is present"""
```

**Configuration Sources** (priority order):
1. Environment variables
2. Config file (YAML)
3. Default values

**Key Configuration Parameters**:
```yaml
llm:
  provider: "gemini"  # or "bedrock"
  gemini:
    api_key: "${LANGEXTRACT_API_KEY}"
    model: "gemini-2.5-pro"
  bedrock:
    region: "${AWS_REGION}"
    model_id: "anthropic.claude-sonnet-4-5-20250929-v1:0"

extraction:
  confidence_threshold: 0.7
  retry_attempts: 1
  batch_size: 10

output:
  directory: "/output"
  csv_encoding: "utf-8"

logging:
  level: "INFO"
  format: "json"
```

---

### 8. Validation Engine (`validator.py`)

**Responsibility**: Validate extracted data against business rules

**Interface**:
```python
class Validator:
    def validate_severity(self, severity: str) -> bool:
        """Validate severity is in allowed values"""
        
    def validate_certainty(self, certainty: str) -> bool:
        """Validate diagnostic certainty"""
        
    def validate_dosage(self, dosage: float) -> bool:
        """Validate dosage is positive"""
        
    def validate_date(self, date_str: str) -> bool:
        """Validate date format and logical consistency"""
        
    def validate_all(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate all data and return errors"""
```

**Validation Rules**:
- Severity: `mild`, `moderate`, `severe`, `critical`
- Diagnostic certainty: `confirmed`, `probable`, `suspected`, `ruled_out`
- Dosages: Must be positive numbers
- Dates: ISO 8601 format, not in future
- Required fields: Must not be NULL

**Design Rationale**:
- Validation occurs after extraction but before CSV export to catch data quality issues early
- Failed validations log warnings but don't block processing (Requirement 11)
- Validation rules align with database CHECK constraints in the schema
- Confidence threshold filtering (default 0.7) can be configured via `EXTRACTION_CONFIDENCE_THRESHOLD` environment variable

---

## Data Models

### Core Data Structures

```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

@dataclass
class ConsultationSession:
    consultation_session_id: UUID
    patient_id: UUID
    doctor_id: UUID
    session_start_datetime: datetime
    full_transcript: str
    transcript_language: str = "en-UK"
    nlp_processed_flag: bool = False

@dataclass
class Symptom:
    symptom_id: UUID
    consultation_session_id: UUID
    patient_id: UUID
    symptom_name: str
    symptom_code: str
    severity: Optional[str]
    duration_days: Optional[int]
    onset_date: Optional[datetime]
    temporal_pattern: Optional[str]
    confidence_score: float
    clinical_modifiers: Optional[Dict]

@dataclass
class Medication:
    prescription_id: UUID
    consultation_session_id: UUID
    patient_id: UUID
    doctor_id: UUID
    medication_name: str
    dosage_value: Optional[int]
    dosage_unit: Optional[str]
    frequency: Optional[str]
    duration_value: Optional[int]
    duration_unit: Optional[str]
    route_of_administration: Optional[str]
    indication: Optional[str]

@dataclass
class Diagnosis:
    assessment_id: UUID
    consultation_session_id: UUID
    patient_id: UUID
    doctor_id: UUID
    assessment_diagnosis: str
    diagnostic_certainty: str
    diagnostic_reasoning: Optional[str]
    key_clinical_features_supporting: Optional[str]
```

### Database Schema Mapping

The system maps to 14 MVP tables from the full database schema:

1. **CONSULTATION_SESSIONS**: Session metadata and full transcript
2. **CONSULTATIONS**: Structured consultation record
3. **SYMPTOMS**: Patient-reported symptoms
4. **MEDICATIONS**: Prescribed medications
5. **ASSOCIATED_FINDINGS**: Objective clinical findings
6. **PHYSICAL_EXAMINATION_FINDINGS**: Physical exam results
7. **REVIEW_OF_SYSTEMS**: Systematic body system review
8. **VITAL_SIGNS**: Clinical measurements
9. **LABORATORY_RESULTS**: Lab test results
10. **CLINICAL_ASSESSMENT_EXTRACTED**: Diagnostic assessment
11. **RED_FLAGS_AND_WARNINGS**: Warning signs
12. **FOLLOW_UP_PLAN_EXTRACTED**: Follow-up instructions
13. **ALLERGIES**: Patient allergies
14. **DIAGNOSES**: Final diagnoses

Plus 2 lookup tables:
- **SEVERITY_LEVELS**: Valid severity values
- **DIAGNOSTIC_CERTAINTY**: Valid certainty levels

---

## Error Handling

### Error Categories

1. **Input Errors**:
   - File not found
   - Invalid file format
   - Encoding errors

2. **Configuration Errors**:
   - Missing API credentials
   - Invalid configuration values
   - Provider unavailable

3. **Extraction Errors**:
   - API rate limits
   - Model errors
   - Low confidence extractions

4. **Validation Errors**:
   - Invalid data values
   - Missing required fields
   - Constraint violations

5. **Export Errors**:
   - File write failures
   - Disk space issues
   - Permission errors

### Error Handling Strategy

```python
class ExtractionError(Exception):
    """Base exception for extraction errors"""
    pass

class ConfigurationError(ExtractionError):
    """Configuration-related errors"""
    pass

class LLMProviderError(ExtractionError):
    """LLM provider errors"""
    pass

class ValidationError(ExtractionError):
    """Data validation errors"""
    pass
```

**Retry Logic**:
- API failures: Exponential backoff (1s, 2s, 4s)
- Rate limits: Wait and retry once
- Transient errors: Retry once
- Fatal errors: Log and exit

**Logging**:
```python
import logging
import json

logger = logging.getLogger(__name__)

# Structured logging
logger.info(json.dumps({
    "event": "extraction_complete",
    "consultation_session_id": str(session_id),
    "entities_extracted": 42,
    "processing_time": 15.3,
    "timestamp": datetime.utcnow().isoformat()
}))
```

---

## Testing Strategy

### Unit Tests

**Test Coverage**:
1. Input Handler: File reading, validation
2. LLM Provider Manager: Provider selection, credential validation
3. Entity Extractor: Each extraction method with mock LLM responses
4. Data Mapper: Schema mapping, UUID generation
5. CSV Exporter: File generation, manifest creation
6. Validator: All validation rules
7. Test Data Generator: Data generation

**Testing Framework**: pytest

**Mock Strategy**:
- Mock LangExtract API calls
- Mock file I/O operations
- Mock environment variables

**Design Rationale**:
- Unit tests focus on core functionality only
- Tests are concise and targeted at critical business logic
- Mocking external dependencies (LLM APIs) ensures fast, reliable tests
- Unit tests may be marked as optional in implementation plan to prioritize MVP delivery

### Integration Tests

**Test Scenarios**:
1. End-to-end extraction with sample consultation
2. Multiple entity types in single consultation
3. Empty consultation (no entities)
4. Malformed input handling
5. API failure and retry
6. CSV export and validation

**Design Rationale**:
- Integration tests validate the complete pipeline from input to CSV output
- Real consultation cases from `consulation_recording_simulation/` directory provide realistic test data
- Tests verify data integrity across the entire extraction-mapping-export workflow

### Test Data

Use provided consultation cases:
- `case_1.md`: Lower back pain (mechanical strain)
- `case_2.md`: Sore throat (bacterial tonsillitis)
- `case_3.md`: (to be provided)
- `case_4.md`: (to be provided)

---

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create output directory
RUN mkdir -p /output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/output

# Entry point
ENTRYPOINT ["python", "-m", "src.main"]
```

**Design Rationale**:
- Python 3.12+ base image (ideally 3.14 when available) for latest language features
- Slim variant reduces image size
- Multi-stage builds not required for this application (simple dependency set)
- Volume mounts for input/output enable flexible file handling
- Environment variables passed at runtime for different configurations
- MCP servers or Docker documentation should be consulted during implementation for best practices

### Docker Compose

```yaml
version: '3.8'

services:
  extractor:
    build: .
    volumes:
      - ./input:/input:ro
      - ./output:/output
    environment:
      - LANGEXTRACT_API_KEY=${LANGEXTRACT_API_KEY}
      - AWS_BEDROCK_ENABLED=${AWS_BEDROCK_ENABLED:-false}
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    command: ["--input", "/input/consultation.md", "--use-test-data"]
```

### Volume Mounts

- `/input`: Read-only mount for input Markdown files
- `/output`: Write mount for CSV outputs
- `/config`: Optional config file mount

---

## Performance Considerations

### Optimization Strategies

1. **Chunking**: Use LangExtract's chunking for long transcripts (>4000 tokens)
2. **Batching**: Extract multiple entity types in parallel where possible
3. **Streaming**: Stream CSV writes to avoid memory issues
4. **Caching**: Cache few-shot examples to avoid reloading

### Performance Targets

- Typical consultation (500-1000 words): <60 seconds (Requirement 12)
- Long consultation (2000+ words): <120 seconds
- Memory usage: <512MB
- CSV generation: <5 seconds

### Monitoring

Log key metrics:
- Processing time per consultation
- Tokens used per extraction
- Entities extracted per type
- API call count and latency
- Error rates

**Design Rationale**:
- LangExtract's chunking strategy handles long transcripts (>4000 tokens) efficiently
- Batching API calls where possible reduces latency
- Streaming CSV writes prevents memory issues with large datasets
- Performance metrics logged to manifest file for tracking and optimization

---

## Security Considerations

1. **API Keys**: Never log or expose API keys
2. **PII Handling**: Transcript contains sensitive patient data
3. **Access Control**: Restrict file system access in container
4. **Data Encryption**: Consider encrypting output CSVs
5. **Audit Trail**: Log all processing activities

---

## Database Architecture Documentation

A complete database schema visualization is provided in `docs/architecture.md`, which includes:

- **Entity Relationship Diagram**: Mermaid diagram showing all 16 MVP tables
- **Table Relationships**: Foreign key connections and cardinality
- **Lookup Tables**: SEVERITY_LEVELS and DIAGNOSTIC_CERTAINTY reference data
- **Data Flow**: How extracted entities map to database tables

**Purpose**: The architecture diagram serves as a visual reference for:
- Understanding table relationships during data mapping implementation
- Verifying foreign key integrity in CSV exports
- Onboarding new developers to the database schema
- Database administrators planning ingestion pipelines

---

## Future Enhancements

1. **Batch Processing**: Process multiple consultations in parallel
2. **Real-time Processing**: Stream processing for live consultations
3. **Quality Metrics**: Track extraction accuracy over time
4. **Active Learning**: Improve few-shot examples based on corrections
5. **Multi-language Support**: Extend beyond English
6. **Direct Database Integration**: Write directly to PostgreSQL instead of CSV
7. **Web API**: REST API for remote extraction requests
8. **UI Dashboard**: Web interface for monitoring and review

---

## Development Workflow

### Project Structure

```
gp-consultation-extractor/
├── src/                              # Source code
│   ├── README.md                     # Module documentation
│   ├── __init__.py
│   ├── main.py
│   ├── input_handler.py
│   ├── llm_provider.py
│   ├── entity_extractor.py
│   ├── data_mapper.py
│   ├── csv_exporter.py
│   ├── test_data_generator.py
│   ├── config_manager.py
│   └── validator.py
├── tests/                            # Test suite
│   ├── README.md                     # Testing documentation
│   ├── __init__.py
│   ├── test_input_handler.py
│   ├── test_entity_extractor.py
│   ├── test_data_mapper.py
│   └── test_integration.py
├── config/                           # Configuration files
│   ├── README.md                     # Configuration guide
│   ├── config.yaml
│   └── few_shot_examples.yaml
├── input/                            # Input consultation files
│   ├── README.md                     # Input format specification
│   └── (consultation markdown files)
├── output/                           # Generated CSV files
│   ├── README.md                     # Output format specification
│   └── (generated CSV files)
├── docs/                             # Documentation
│   └── architecture.md               # Database architecture diagram
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Version Control Strategy

**Commit Frequency**: After completing each task or sub-task from the implementation plan

**Commit Message Format**:
```
[Task X.Y] Brief description of what was implemented

- Detailed change 1
- Detailed change 2
- References: Requirement X.Y
```

**Example Commits**:
- `[Task 1.1] Set up project structure and core interfaces`
- `[Task 2.2] Implement User model with validation`
- `[Task 3.1] Add database connection utilities`

**Rationale**: Small, incremental commits provide:
- Clear development history for code review
- Easy rollback to working states
- Better collaboration and conflict resolution
- Traceable link between tasks and code changes

### Subfolder Documentation

Each major directory contains a README.md file explaining its purpose and structure:

- **src/README.md**: Module documentation, component responsibilities, and usage examples
- **tests/README.md**: Testing strategy, how to run tests, and test data requirements
- **config/README.md**: Configuration options, environment variables, and few-shot example format
- **input/README.md**: Input file format specification and validation rules
- **output/README.md**: Output CSV format, manifest structure, and database ingestion guide
- **docs/architecture.md**: Complete database schema visualization with Mermaid diagrams showing table relationships

### Dependencies

```
langextract>=0.1.0
pandas>=2.0.0
pyyaml>=6.0
boto3>=1.28.0  # For AWS Bedrock
google-generativeai>=0.3.0  # For Gemini
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-mock>=3.11.0
```

### Development Tools

- **Linting**: ruff
- **Formatting**: black
- **Type Checking**: mypy
- **Testing**: pytest with coverage
- **Documentation**: Sphinx
- **Information Access**: MCP servers for accessing current documentation (LangExtract, AWS Bedrock, PostgreSQL, Docker)

---

## Deployment

### Environment Variables

Required:
- `LANGEXTRACT_API_KEY` (for Gemini) OR
- `AWS_BEDROCK_ENABLED=true` + `AWS_REGION` (for Bedrock)

Optional:
- `MODEL_ID`: Override default model
- `EXTRACTION_CONFIDENCE_THRESHOLD`: Filter low-confidence extractions (default: 0.7)
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `OUTPUT_DIR`: Output directory (default: /output)

### Running the Container

```bash
# Build
docker build -t gp-extractor .

# Run with Gemini
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
  -e LANGEXTRACT_API_KEY=your-key \
  gp-extractor --input /input/consultation.md --use-test-data

# Run with AWS Bedrock
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
  -e AWS_BEDROCK_ENABLED=true \
  -e AWS_REGION=us-east-1 \
  -v ~/.aws:/root/.aws:ro \
  gp-extractor --input /input/consultation.md
```

### Exit Codes

- `0`: Success
- `1`: Input error
- `2`: Configuration error
- `3`: Extraction error
- `4`: Validation error
- `5`: Export error
