# GP Consultation Data Extraction System

A Python-based system that extracts structured clinical data from unstructured GP consultation transcripts using LangExtract with LLM-powered NLP. The system maps extracted entities to a PostgreSQL database schema and exports data as CSV files for database ingestion.

## Features

- **Multi-LLM Support**: Works with Google Gemini 2.5 Pro or AWS Bedrock Claude Sonnet 4.5
- **Comprehensive Entity Extraction**: Extracts symptoms, medications, diagnoses, vital signs, physical exam findings, red flags, and follow-up plans
- **Database Schema Mapping**: Maps extracted entities to 14 PostgreSQL tables with proper foreign key relationships
- **CSV Export**: Generates CSV files ready for database ingestion with proper encoding and JSONB serialization
- **Test Data Generation**: One-click generation of realistic UK patient and doctor data
- **Docker Support**: Containerized deployment for consistent execution
- **Robust Error Handling**: Comprehensive error handling with retry logic and detailed logging
- **Validation**: Comprehensive data validation against business rules with proper error reporting

## Installation

### Prerequisites

- Python 3.12 or higher
- Docker (optional, for containerized deployment)
- LangExtract API key (for Gemini) OR AWS credentials (for Bedrock)

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gp-consultation-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# For Gemini
export LANGEXTRACT_API_KEY="your-api-key-here"

# OR for AWS Bedrock
export AWS_BEDROCK_ENABLED=true
export AWS_REGION=us-east-1
# Ensure AWS credentials are configured (~/.aws/credentials)
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t gp-extractor .
```

2. Or use Docker Compose:
```bash
docker-compose build
```

## Usage

### Command-Line Usage

#### With Test Data (Recommended for Testing)

```bash
python -m src.main --input input/case_1.md --use-test-data
```

This automatically generates realistic patient and doctor data.

#### With Existing Patient/Doctor IDs

```bash
python -m src.main \
  --input input/case_1.md \
  --patient-id "123e4567-e89b-12d3-a456-426614174000" \
  --doctor-id "987fcdeb-51a2-43f7-8c9d-123456789abc"
```

#### Custom Output Directory

```bash
python -m src.main \
  --input input/case_1.md \
  --use-test-data \
  --output-dir /path/to/output
```

### Docker Usage

#### Using Docker Run

```bash
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
  -e LANGEXTRACT_API_KEY=your-key \
  gp-extractor --input /input/case_1.md --use-test-data
```

#### Using Docker Compose

1. Edit `docker-compose.yml` to set your API key
2. Place your consultation file in `input/consultation.md`
3. Run:

```bash
docker-compose up
```

The CSV files will be generated in the `output/` directory.

### AWS Bedrock Usage

The system supports both standard AWS Bedrock (via boto3) and custom API Gateway endpoints:

**Standard Bedrock (boto3):**
```bash
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_BEDROCK_ENABLED=true \
  -e AWS_REGION=us-east-1 \
  -e MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0 \
  gp-extractor --input /input/case_1.md --use-test-data
```

**Custom API Gateway Endpoint:**
```bash
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
  -e AWS_BEDROCK_ENABLED=true \
  -e BEDROCK_API_ENDPOINT=https://your-api-gateway-url \
  -e BEDROCK_API_KEY=your-api-key \
  -e BEDROCK_TEAM_ID=your-team-id \
  -e MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0 \
  gp-extractor --input /input/case_1.md --use-test-data
```

The system automatically uses the appropriate Bedrock client based on configuration.

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LANGEXTRACT_API_KEY` | API key for Gemini | - | Yes (if using Gemini) |
| `AWS_BEDROCK_ENABLED` | Enable AWS Bedrock | `false` | No |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` | No |
| `MODEL_ID` | Bedrock model ID | `anthropic.claude-sonnet-4-5-20250929-v1:0` | No |
| `EXTRACTION_CONFIDENCE_THRESHOLD` | Minimum confidence for extractions | `0.7` | No |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `OUTPUT_DIR` | Output directory | `output` | No |

### Configuration File

Edit `config/config.yaml` to customize:

- LLM provider settings
- Extraction parameters
- Output settings
- Logging configuration

See `config/README.md` for detailed configuration options.

## Input Format

Consultation transcripts should be in Markdown format with patient-GP dialogue. Example:

```markdown
# GP Consultation - Lower Back Pain

**Patient**: I've had this pain in my lower back since yesterday morning...

**GP**: Can you describe the pain for me?

**Patient**: It's a sharp pain when I move or bend...
```

See `input/README.md` for detailed format specification.

## Output

The system generates:

1. **CSV Files**: One file per database table
   - `consultation_sessions.csv`
   - `consultations.csv`
   - `symptoms.csv`
   - `medications.csv`
   - `diagnoses.csv`
   - `clinical_assessment_extracted.csv`
   - `vital_signs.csv`
   - `physical_examination_findings.csv`
   - `red_flags_and_warnings.csv`
   - `follow_up_plan_extracted.csv`

2. **Manifest File**: `manifest.json` with extraction metadata

See `output/README.md` for detailed output format and database ingestion guide.

## Database Schema

The system maps to 14 PostgreSQL tables:

- **Core Tables**: `CONSULTATION_SESSIONS`, `CONSULTATIONS`
- **Clinical Entities**: `SYMPTOMS`, `MEDICATIONS`, `DIAGNOSES`
- **Examinations**: `VITAL_SIGNS`, `PHYSICAL_EXAMINATION_FINDINGS`
- **Assessments**: `CLINICAL_ASSESSMENT_EXTRACTED`, `RED_FLAGS_AND_WARNINGS`, `FOLLOW_UP_PLAN_EXTRACTED`
- **Lookup Tables**: `SEVERITY_LEVELS`, `DIAGNOSTIC_CERTAINTY`

See `docs/architecture.md` for complete database schema with ER diagram.

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Input error (file not found, invalid format) |
| 2 | Configuration error (missing credentials) |
| 3 | Extraction error (API failure) |
| 4 | Validation error (invalid data) |
| 5 | Export error (file write failure) |

## Examples

### Example 1: Extract from Case 1 (Lower Back Pain)

```bash
python -m src.main --input input/case_1.md --use-test-data
```

Output:
```
2024-11-16 10:30:00 - INFO - Starting GP Consultation Data Extraction System
2024-11-16 10:30:01 - INFO - Using LLM provider: gemini
2024-11-16 10:30:02 - INFO - Extracted 42 entities
2024-11-16 10:30:03 - INFO - Exported 10 CSV files to output
2024-11-16 10:30:03 - INFO - Processing complete in 3.45 seconds
```

### Example 2: Extract from Case 2 (Sore Throat)

```bash
python -m src.main --input input/case_2.md --use-test-data
```

## Testing

Run all tests (161 tests):
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run integration tests:
```bash
pytest tests/test_integration.py
```

**Test Status:** ✅ All 161 tests passing
- 85+ unit tests
- 20+ integration tests
- 91% code coverage

See `tests/README.md` and `TESTING.md` for detailed testing guide.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Main Application                         │  │
│  │  Input → LLM Provider → Entity Extractor →           │  │
│  │  Data Mapper → Validator → CSV Exporter              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ↑ Input                              ↓ Output
    [Markdown Files]                    [CSV Files + Manifest]
```

## Performance

- Typical consultation (500-1000 words): <60 seconds
- Long consultation (2000+ words): <120 seconds
- Memory usage: <512MB

## Troubleshooting

### API Key Issues

```bash
# Verify API key is set
echo $LANGEXTRACT_API_KEY

# Test API connection
python -c "import os; print('API key set' if os.getenv('LANGEXTRACT_API_KEY') else 'API key missing')"
```

### Docker Issues

```bash
# Check Docker is running
docker ps

# View container logs
docker-compose logs

# Rebuild image
docker-compose build --no-cache
```

### Extraction Errors

- Check input file format matches specification
- Verify API credentials are valid
- Check network connectivity
- Review logs for detailed error messages

## Contributing

See `CONTRIBUTING.md` for development guidelines.

## License

See `LICENSE` file for details.

## Support

For issues and questions:
- Check `docs/` directory for detailed documentation
- Review error logs in console output
- Verify configuration in `config/config.yaml`

## Acknowledgments

- Built with [LangExtract](https://github.com/AnswerDotAI/langextract) for clinical entity extraction
- Uses Google Gemini 2.5 Pro or AWS Bedrock Claude Sonnet 4.5 for NLP
- Database schema designed for PostgreSQL 14+
