# Configuration

This directory contains configuration files for the GP Consultation Data Extraction System.

## Configuration Files

### `config.yaml`
Main configuration file for application settings.

**Structure**:
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

### `few_shot_examples.yaml`
Few-shot learning examples for LangExtract entity extraction.

**Structure**:
```yaml
medications:
  - extraction_text: "Patient takes Aspirin 100mg daily for heart health."
    extractions:
      - extraction_class: "medication"
        text: "Aspirin"
        attributes:
          medication_group: "Aspirin"
      - extraction_class: "dosage"
        text: "100mg"
        attributes:
          medication_group: "Aspirin"
      - extraction_class: "frequency"
        text: "daily"
        attributes:
          medication_group: "Aspirin"

symptoms:
  - extraction_text: "Patient reports severe headache for 3 days."
    extractions:
      - extraction_class: "symptom_name"
        text: "headache"
        attributes:
          symptom_group: "headache_1"
      - extraction_class: "severity"
        text: "severe"
        attributes:
          symptom_group: "headache_1"
```

## Environment Variables

### Required Variables

#### For Gemini API:
```bash
LANGEXTRACT_API_KEY="your-gemini-api-key"
```

#### For AWS Bedrock:
```bash
AWS_BEDROCK_ENABLED=true
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID="your-access-key"
AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### Optional Variables

```bash
# Override default model
MODEL_ID="anthropic.claude-sonnet-4-5-20250929-v1:0"

# Filter low-confidence extractions
EXTRACTION_CONFIDENCE_THRESHOLD=0.7

# Logging configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Output directory
OUTPUT_DIR="/output"
```

## Configuration Priority

Configuration values are loaded in the following priority order (highest to lowest):

1. **Environment Variables**: Override all other sources
2. **Config File**: Values from `config.yaml`
3. **Default Values**: Hardcoded defaults in the application

**Example**:
```python
# If LANGEXTRACT_API_KEY is set in environment, it overrides config.yaml
api_key = os.getenv("LANGEXTRACT_API_KEY") or config.get("llm.gemini.api_key")
```

## LLM Provider Configuration

### Gemini Configuration

**Required**:
- `LANGEXTRACT_API_KEY`: Your Gemini API key

**Optional**:
- `MODEL_ID`: Override default model (default: `gemini-2.5-pro`)

**Example**:
```bash
export LANGEXTRACT_API_KEY="AIza..."
python -m src.main --input input/consultation.md
```

### AWS Bedrock Configuration

**Required**:
- `AWS_BEDROCK_ENABLED=true`: Enable Bedrock provider
- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

**Optional**:
- `MODEL_ID`: Override default model (default: `anthropic.claude-sonnet-4-5-20250929-v1:0`)

**Example**:
```bash
export AWS_BEDROCK_ENABLED=true
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
python -m src.main --input input/consultation.md
```

## Few-Shot Example Format

Few-shot examples teach the LLM how to extract entities correctly.

### Example Structure

Each example contains:
- `extraction_text`: The text to extract from
- `extractions`: List of extracted entities with:
  - `extraction_class`: Type of entity (e.g., "medication", "dosage")
  - `text`: The extracted text span
  - `attributes`: Grouping attributes (e.g., `medication_group`)

### Grouping Attributes

Use grouping attributes to link related extractions:
- `medication_group`: Links medication name, dosage, frequency, etc.
- `symptom_group`: Links symptom name, severity, duration, etc.
- `diagnosis_group`: Links diagnosis name, certainty, features, etc.

**Example**:
```yaml
medications:
  - extraction_text: "Prescribed Amoxicillin 500mg three times daily for 7 days for bacterial infection."
    extractions:
      - extraction_class: "medication"
        text: "Amoxicillin"
        attributes:
          medication_group: "Amoxicillin"
      - extraction_class: "dosage"
        text: "500mg"
        attributes:
          medication_group: "Amoxicillin"
      - extraction_class: "frequency"
        text: "three times daily"
        attributes:
          medication_group: "Amoxicillin"
      - extraction_class: "duration"
        text: "7 days"
        attributes:
          medication_group: "Amoxicillin"
      - extraction_class: "indication"
        text: "bacterial infection"
        attributes:
          medication_group: "Amoxicillin"
```

## Extraction Parameters

### Confidence Threshold
Filter extractions below a confidence score:
```yaml
extraction:
  confidence_threshold: 0.7  # 0.0 to 1.0
```

### Retry Attempts
Number of retries for failed API calls:
```yaml
extraction:
  retry_attempts: 1  # Retry once on failure
```

### Batch Size
Number of entities to process in parallel:
```yaml
extraction:
  batch_size: 10
```

## Output Configuration

### Output Directory
```yaml
output:
  directory: "/output"  # Path to output directory
```

### CSV Encoding
```yaml
output:
  csv_encoding: "utf-8"  # Character encoding for CSV files
```

## Logging Configuration

### Log Level
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Format
```yaml
logging:
  format: "json"  # json or text
```

**JSON Format Example**:
```json
{
  "timestamp": "2025-11-16T10:30:00Z",
  "level": "INFO",
  "event": "extraction_complete",
  "entities_extracted": 42,
  "processing_time": 15.3
}
```

## Validation

The application validates configuration on startup:
- Required environment variables are present
- API credentials are valid
- Output directory is writable
- Config file syntax is correct

**Validation Errors**:
```
ConfigurationError: LANGEXTRACT_API_KEY not found in environment
ConfigurationError: Invalid confidence_threshold: must be between 0.0 and 1.0
```

## Best Practices

1. **Never commit API keys**: Use environment variables or `.env` files (add to `.gitignore`)
2. **Use separate configs for environments**: dev, staging, production
3. **Document custom configurations**: Add comments to `config.yaml`
4. **Test configuration changes**: Validate before deployment
5. **Keep few-shot examples updated**: Add new examples as you discover edge cases
