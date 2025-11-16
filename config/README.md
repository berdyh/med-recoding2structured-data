# Configuration Documentation

This directory contains configuration files for the GP Consultation Data Extraction System.

## Configuration Files

### config.yaml

Main configuration file with default settings for:
- LLM provider settings (Gemini and Bedrock)
- Extraction parameters
- Output settings
- Logging configuration

### few_shot_examples.yaml

Few-shot learning examples for entity extraction:
- Medication extraction examples
- Symptom extraction examples
- Diagnosis extraction examples
- Vital signs extraction examples
- Physical exam extraction examples
- Red flags extraction examples
- Follow-up plan extraction examples

## config.yaml Structure

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
  directory: "output"
  csv_encoding: "utf-8"

logging:
  level: "INFO"
  format: "json"
```

## Environment Variables

Configuration values can be overridden with environment variables. Environment variables take precedence over config file values.

### Required Variables

#### For Gemini (Default)

```bash
export LANGEXTRACT_API_KEY="your-gemini-api-key"
```

#### For AWS Bedrock

```bash
export AWS_BEDROCK_ENABLED=true
export AWS_REGION="us-east-1"
# AWS credentials should be configured in ~/.aws/credentials
```

### Optional Variables

```bash
# Override model
export MODEL_ID="gemini-2.5-pro"  # or "anthropic.claude-sonnet-4-5-20250929-v1:0"

# Extraction settings
export EXTRACTION_CONFIDENCE_THRESHOLD=0.7
export EXTRACTION_RETRY_ATTEMPTS=1

# Output settings
export OUTPUT_DIR="output"
export CSV_ENCODING="utf-8"

# Logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

## LLM Provider Configuration

### Gemini Configuration

**API Key**: Obtain from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Supported Models**:
- `gemini-2.5-pro` (recommended)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

**Configuration**:
```yaml
llm:
  provider: "gemini"
  gemini:
    api_key: "${LANGEXTRACT_API_KEY}"
    model: "gemini-2.5-pro"
```

**Environment Setup**:
```bash
export LANGEXTRACT_API_KEY="your-api-key"
```

### AWS Bedrock Configuration

**Prerequisites**:
- AWS account with Bedrock access
- AWS credentials configured (`~/.aws/credentials`)
- Bedrock model access enabled in AWS console

**Supported Models**:
- `anthropic.claude-sonnet-4-5-20250929-v1:0` (recommended)
- `anthropic.claude-3-5-sonnet-20240620-v1:0`
- `anthropic.claude-3-opus-20240229-v1:0`

**Configuration**:
```yaml
llm:
  provider: "bedrock"
  bedrock:
    region: "${AWS_REGION}"
    model_id: "anthropic.claude-sonnet-4-5-20250929-v1:0"
```

**Environment Setup**:
```bash
export AWS_BEDROCK_ENABLED=true
export AWS_REGION="us-east-1"

# Ensure AWS credentials are configured
aws configure
```

## Extraction Parameters

### confidence_threshold

Minimum confidence score for extracted entities (0.0 to 1.0).

- **Default**: 0.7
- **Range**: 0.0 - 1.0
- **Recommendation**: 0.7 for production, 0.5 for testing

Lower values include more entities but may have lower accuracy.

### retry_attempts

Number of retry attempts for failed API calls.

- **Default**: 1
- **Range**: 0 - 5
- **Recommendation**: 1 for production, 0 for testing

### batch_size

Number of entities to process in a single batch (future feature).

- **Default**: 10
- **Range**: 1 - 100

## Output Settings

### directory

Output directory for CSV files.

- **Default**: `output`
- **Example**: `/path/to/output`

### csv_encoding

Character encoding for CSV files.

- **Default**: `utf-8`
- **Options**: `utf-8`, `utf-16`, `latin-1`

## Logging Configuration

### level

Logging verbosity level.

- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Recommendations**:
- `DEBUG`: Development and troubleshooting
- `INFO`: Production (default)
- `WARNING`: Production with minimal logging
- `ERROR`: Production with error-only logging

### format

Log message format.

- **Default**: `json`
- **Options**: `json`, `text`

**JSON Format** (recommended for production):
```json
{
  "timestamp": "2024-11-16T10:30:00Z",
  "level": "INFO",
  "message": "Extraction complete",
  "entities_extracted": 42
}
```

**Text Format** (easier for development):
```
2024-11-16 10:30:00 - INFO - Extraction complete
```

## Few-Shot Examples Format

The `few_shot_examples.yaml` file contains training examples for the LLM to learn entity extraction patterns.

### Example Structure

```yaml
medications:
  - text: "Patient takes Aspirin 100mg daily for heart health."
    extractions:
      - class: "medication"
        text: "Aspirin"
        attributes:
          medication_group: "med_1"
      - class: "dosage"
        text: "100mg"
        attributes:
          medication_group: "med_1"
      - class: "frequency"
        text: "daily"
        attributes:
          medication_group: "med_1"
      - class: "indication"
        text: "heart health"
        attributes:
          medication_group: "med_1"
```

### Entity Types

#### Medications

**Classes**: `medication`, `dosage`, `route`, `frequency`, `duration`, `indication`

**Attributes**: `medication_group` (links related information)

#### Symptoms

**Classes**: `symptom_name`, `severity`, `duration`, `onset`, `temporal_pattern`

**Attributes**: `symptom_group` (links related information)

#### Diagnoses

**Classes**: `diagnosis`, `certainty`, `clinical_features`

**Attributes**: `diagnosis_group` (links related information)

#### Vital Signs

**Classes**: `temperature`, `blood_pressure`, `heart_rate`, `oxygen_saturation`, `respiratory_rate`

**Attributes**: None (typically extracted as a group)

#### Physical Exam

**Classes**: `examination_type`, `anatomical_site`, `findings`, `severity`

**Attributes**: `exam_group` (links related information)

#### Red Flags

**Classes**: `warning_description`, `warning_type`, `severity`

**Attributes**: `warning_group` (links related information)

#### Follow-up

**Classes**: `follow_up_type`, `timing`, `condition`, `action`, `priority`

**Attributes**: `followup_group` (links related information)

### Adding Custom Examples

To improve extraction accuracy, add more examples:

1. Identify extraction errors in output
2. Create example with correct extraction
3. Add to appropriate section in `few_shot_examples.yaml`
4. Test with new consultation

**Example**:
```yaml
symptoms:
  - text: "I've had a persistent cough for three weeks."
    extractions:
      - class: "symptom_name"
        text: "cough"
        attributes:
          symptom_group: "sym_1"
      - class: "temporal_pattern"
        text: "persistent"
        attributes:
          symptom_group: "sym_1"
      - class: "duration"
        text: "three weeks"
        attributes:
          symptom_group: "sym_1"
```

## Configuration Priority

Configuration values are loaded in this order (later overrides earlier):

1. **Default values** (hardcoded in application)
2. **config.yaml** file
3. **Environment variables**

Example:
```yaml
# config.yaml
extraction:
  confidence_threshold: 0.7
```

```bash
# Environment variable overrides config file
export EXTRACTION_CONFIDENCE_THRESHOLD=0.8
```

Result: `confidence_threshold = 0.8`

## Validation

The application validates configuration on startup:

- Required fields are present
- Values are in valid ranges
- API credentials are valid
- File paths exist

Validation errors will cause the application to exit with code 2.

## Docker Configuration

When using Docker, pass environment variables:

```bash
docker run \
  -e LANGEXTRACT_API_KEY=your-key \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/config:/app/config \
  gp-extractor --input /input/case_1.md
```

Or use docker-compose.yml:

```yaml
environment:
  - LANGEXTRACT_API_KEY=${LANGEXTRACT_API_KEY}
  - LOG_LEVEL=${LOG_LEVEL:-INFO}
```

## Troubleshooting

### Configuration Not Loading

- Check file path: `ls config/config.yaml`
- Verify YAML syntax: `python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"`
- Check file permissions: `ls -l config/config.yaml`

### Environment Variables Not Working

- Verify variable is set: `echo $LANGEXTRACT_API_KEY`
- Check variable name matches exactly
- Restart application after setting variables

### API Credentials Invalid

- Verify API key format
- Check API key has not expired
- Test API connection separately
- For Bedrock, verify AWS credentials: `aws sts get-caller-identity`

## Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Keep few-shot examples** up to date with real-world cases
4. **Test configuration changes** before deploying
5. **Document custom configurations** for your team

## Example Configurations

### Development

```yaml
llm:
  provider: "gemini"
  gemini:
    model: "gemini-2.5-pro"

extraction:
  confidence_threshold: 0.5  # Lower for testing
  retry_attempts: 0  # Faster failures

logging:
  level: "DEBUG"  # Verbose logging
```

### Production

```yaml
llm:
  provider: "bedrock"
  bedrock:
    region: "us-east-1"
    model_id: "anthropic.claude-sonnet-4-5-20250929-v1:0"

extraction:
  confidence_threshold: 0.7  # Higher accuracy
  retry_attempts: 1  # Retry on failure

logging:
  level: "INFO"  # Standard logging
  format: "json"  # Structured logs
```

### Testing

```yaml
llm:
  provider: "gemini"
  gemini:
    model: "gemini-1.5-flash"  # Faster, cheaper

extraction:
  confidence_threshold: 0.6
  retry_attempts: 0

logging:
  level: "WARNING"  # Minimal logging
```
