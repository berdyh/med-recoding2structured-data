# GP Consultation Data Extraction System

A Python-based system that extracts structured clinical data from unstructured GP consultation transcripts using LangExtract with LLM-powered NLP. The system maps extracted entities to a PostgreSQL database schema and exports data as CSV files for database ingestion.

## Features

- **Multi-LLM Support**: Works with Google Gemini 2.5 Pro or Claude Sonnet 4.5 via AWS Bedrock
- **Clinical Entity Extraction**: Extracts symptoms, medications, diagnoses, vital signs, physical exam findings, red flags, and follow-up plans
- **Database Schema Mapping**: Maps extracted data to 14 PostgreSQL tables with proper foreign key relationships
- **CSV Export**: Generates one CSV file per database table with manifest file
- **Test Data Generation**: One-click generation of realistic patient and doctor data
- **Docker Support**: Fully containerized for consistent deployment
- **Comprehensive Logging**: Structured JSON logging with detailed error handling

## Project Structure

```
gp-consultation-extractor/
├── src/                    # Source code modules
├── tests/                  # Test suite
├── config/                 # Configuration files
├── input/                  # Input consultation files
├── output/                 # Generated CSV files
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
└── README.md              # This file
```

## Installation

### Local Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Installation

1. Build the Docker image:
   ```bash
   docker-compose build
   ```

## Configuration

### Environment Variables

#### For Gemini API:
```bash
export LANGEXTRACT_API_KEY="your-gemini-api-key"
```

#### For AWS Bedrock:
```bash
export AWS_BEDROCK_ENABLED=true
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

#### Optional Configuration:
```bash
export MODEL_ID="anthropic.claude-sonnet-4-5-20250929-v1:0"  # Override default model
export EXTRACTION_CONFIDENCE_THRESHOLD=0.7  # Filter low-confidence extractions
export LOG_LEVEL=INFO  # Logging level
```

### Configuration File

Edit `config/config.yaml` to customize extraction parameters, output settings, and logging configuration.

## Usage

### Local Execution

#### With test data generation:
```bash
python -m src.main --input input/consultation.md --use-test-data
```

#### With specific patient/doctor IDs:
```bash
python -m src.main --input input/consultation.md
```

### Docker Execution

#### With test data generation:
```bash
docker-compose up
```

#### With custom input file:
```bash
docker-compose run extractor --input /input/your-consultation.md --use-test-data
```

## Output

The system generates:
- One CSV file per database table in the `output/` directory
- A `manifest.json` file listing all generated files with metadata
- Structured logs with extraction statistics

### Output Files

- `consultation_sessions.csv`
- `consultations.csv`
- `symptoms.csv`
- `medications.csv`
- `diagnoses.csv`
- `vital_signs.csv`
- `physical_examination_findings.csv`
- `red_flags_and_warnings.csv`
- `follow_up_plan_extracted.csv`
- And more (see `output/README.md` for complete list)

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

## Documentation

- **src/README.md**: Module documentation and component responsibilities
- **tests/README.md**: Testing strategy and how to run tests
- **config/README.md**: Configuration options and environment variables
- **input/README.md**: Input file format specification
- **output/README.md**: Output CSV format and database ingestion guide
- **docs/architecture.md**: Database schema visualization with Mermaid diagrams

## Requirements

- Python 3.12+
- LangExtract API key (Gemini) or AWS Bedrock credentials
- See `requirements.txt` for complete dependency list

## License

[Add your license here]

## Support

For issues and questions, please refer to the documentation in the `docs/` directory.
