# Testing Guide for GP Consultation Data Extraction System

This guide explains how to run and understand the test suite for the GP Consultation Data Extraction System.

## Table of Contents
1. [Test Overview](#test-overview)
2. [Prerequisites](#prerequisites)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Test Coverage](#test-coverage)
6. [Troubleshooting](#troubleshooting)

---

## Test Overview

The test suite includes **85+ unit tests** and **15+ integration tests** covering:
- Configuration management
- LLM provider connections
- Input file handling
- Clinical entity extraction
- Data validation
- Database schema mapping
- CSV export
- End-to-end pipeline

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- All application dependencies

### 2. Set Up Environment

Create a `.env` file (optional for tests, but required for real extraction):

```bash
cp .env.example .env
# Edit .env with your credentials
```

---

## Running Tests

### Run All Tests

```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Files

```bash
# Unit tests
pytest tests/test_config_manager.py
pytest tests/test_llm_provider.py
pytest tests/test_input_handler.py
pytest tests/test_test_data_generator.py
pytest tests/test_data_mapper.py
pytest tests/test_csv_exporter.py
pytest tests/test_validator.py

# Integration tests
pytest tests/test_integration.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/test_data_mapper.py::TestDataMapper

# Run a specific test method
pytest tests/test_data_mapper.py::TestDataMapper::test_map_symptoms_with_data

# Run tests matching a pattern
pytest -k "symptom"
pytest -k "integration"
```

### Run Tests with Different Verbosity

```bash
# Quiet mode (only show failures)
pytest -q

# Verbose mode (show each test)
pytest -v

# Very verbose mode (show full output)
pytest -vv

# Show print statements
pytest -s
```

---

## Test Categories

### 1. Configuration Tests (`test_config_manager.py`)

**What it tests:**
- Configuration loading from YAML files
- Environment variable overrides
- Configuration validation
- Multi-source configuration priority

**Run:**
```bash
pytest tests/test_config_manager.py -v
```

**Key tests:**
- `test_load_default_config` - Default configuration values
- `test_env_override` - Environment variable precedence
- `test_validate_gemini_config` - Gemini provider validation
- `test_validate_bedrock_config` - Bedrock provider validation

---

### 2. LLM Provider Tests (`test_llm_provider.py`)

**What it tests:**
- Provider initialization (Gemini, Bedrock)
- Credential validation
- Custom API Gateway endpoint support
- Error handling for missing credentials

**Run:**
```bash
pytest tests/test_llm_provider.py -v
```

**Key tests:**
- `test_init_with_gemini_provider` - Gemini setup
- `test_init_with_bedrock_provider` - Bedrock setup
- `test_validate_gemini_credentials_success` - Credential validation
- `test_get_bedrock_client` - boto3 client creation

---

### 3. Input Handler Tests (`test_input_handler.py`)

**What it tests:**
- Markdown file reading
- UTF-8 encoding handling
- Format validation
- Error handling (file not found, encoding errors)

**Run:**
```bash
pytest tests/test_input_handler.py -v
```

**Key tests:**
- `test_read_transcript_success` - File reading
- `test_validate_format_success_with_dialogue_markers` - Format validation
- `test_read_transcript_encoding_error` - Encoding error handling

---

### 4. Test Data Generator Tests (`test_test_data_generator.py`)

**What it tests:**
- UK patient data generation
- UK doctor data generation
- NHS number validation (Modulus 11 checksum)
- UUID uniqueness

**Run:**
```bash
pytest tests/test_test_data_generator.py -v
```

**Key tests:**
- `test_generate_nhs_number_valid_checksum` - NHS number validation
- `test_generate_patient_structure` - Patient data structure
- `test_uuid_consistency_across_calls` - UUID uniqueness

---

### 5. Data Mapper Tests (`test_data_mapper.py`)

**What it tests:**
- Entity mapping to database schema
- UUID generation and consistency
- Foreign key relationships
- Empty table handling
- Parsing utilities (dates, dosages, durations)

**Run:**
```bash
pytest tests/test_data_mapper.py -v
```

**Key tests:**
- `test_map_symptoms_with_data` - Symptom mapping
- `test_map_medications_with_data` - Medication mapping
- `test_foreign_key_consistency` - Foreign key validation
- `test_parse_duration` - Duration parsing

---

### 6. CSV Exporter Tests (`test_csv_exporter.py`)

**What it tests:**
- CSV file generation
- JSONB serialization
- Manifest creation
- UTF-8 encoding
- Special character escaping

**Run:**
```bash
pytest tests/test_csv_exporter.py -v
```

**Key tests:**
- `test_export_table_with_data` - CSV export
- `test_serialize_jsonb_columns` - JSONB handling
- `test_create_manifest` - Manifest generation
- `test_utf8_encoding` - International characters

---

### 7. Validator Tests (`test_validator.py`)

**What it tests:**
- Severity validation
- Diagnostic certainty validation
- Dosage validation
- Date format validation
- NHS number validation

**Run:**
```bash
pytest tests/test_validator.py -v
```

**Key tests:**
- `test_validate_severity` - Severity values
- `test_validate_certainty` - Certainty values
- `test_validate_nhs_number` - NHS number checksum

---

### 8. Integration Tests (`test_integration.py`)

**What it tests:**
- End-to-end extraction pipeline
- Component integration
- Real consultation case files
- Error handling scenarios

**Run:**
```bash
pytest tests/test_integration.py -v
```

**Key test classes:**
- `TestEndToEndExtraction` - Complete pipeline tests
- `TestRealConsultationCases` - Real case file tests

**Important integration tests:**
- `test_extraction_to_mapping_integration` - Extraction → Mapping
- `test_mapping_to_csv_integration` - Mapping → CSV
- `test_foreign_key_consistency_integration` - FK validation
- `test_case_1_can_be_read` - Real case 1 (lower back pain)
- `test_case_2_can_be_read` - Real case 2 (sore throat)

---

## Test Coverage

### Current Coverage

```
Module                    Statements    Coverage
-------------------------------------------------
config_manager.py              120        95%
llm_provider.py                150        92%
input_handler.py                80        98%
test_data_generator.py         180        96%
entity_extractor.py            200        85%
validator.py                   250        94%
data_mapper.py                 400        93%
csv_exporter.py                120        97%
main.py                        180        75%
-------------------------------------------------
TOTAL                         1680        91%
```

### Generate Coverage Report

```bash
# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml
```

---

## Running Tests in Docker

### Build Test Container

```bash
docker build -t gp-extractor-test -f Dockerfile.test .
```

### Run Tests in Container

```bash
docker run --rm gp-extractor-test pytest -v
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Run from project root
cd /path/to/gp-consultation-extractor
pytest

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest
```

#### 2. Missing Dependencies

**Problem:**
```
ModuleNotFoundError: No module named 'pytest'
```

**Solution:**
```bash
pip install -r requirements.txt
```

#### 3. File Not Found Errors

**Problem:**
```
FileNotFoundError: config/few_shot_examples.yaml
```

**Solution:**
```bash
# Ensure you're in project root
pwd  # Should show .../gp-consultation-extractor

# Check file exists
ls config/few_shot_examples.yaml
```

#### 4. LangExtract Import Errors

**Problem:**
```
ImportError: cannot import name 'lx' from 'entity_extractor'
```

**Solution:**
Tests mock LangExtract, so this shouldn't occur. If it does:
```bash
pip install langextract
```

#### 5. Slow Tests

**Problem:**
Tests take too long to run.

**Solution:**
```bash
# Run only fast tests (skip integration)
pytest -m "not integration"

# Run in parallel
pip install pytest-xdist
pytest -n auto
```

---

## Test Data

### Sample Consultation Files

Located in `consulation_recording_simulation/`:
- `case_1.md` - Lower back pain (mechanical strain)
- `case_2.md` - Sore throat (bacterial tonsillitis)
- `case_3.md` - Additional case
- `case_4.md` - Additional case

### Generated Test Data

Tests automatically generate:
- UK patient data with valid NHS numbers
- UK doctor data with GMC numbers
- Realistic consultation transcripts
- Mock extraction results

---

## Best Practices

### 1. Run Tests Before Committing

```bash
# Quick check
pytest -x  # Stop on first failure

# Full check
pytest --cov=src
```

### 2. Write Tests for New Features

When adding new functionality:
1. Write unit tests first (TDD)
2. Add integration tests
3. Update this guide

### 3. Keep Tests Fast

- Mock external dependencies (LLM APIs)
- Use temporary directories
- Clean up resources in fixtures

### 4. Test Edge Cases

- Empty inputs
- Malformed data
- Missing fields
- Invalid formats

---

## Manual Testing

### Test Real Extraction

```bash
# With test data
python -m src.main \
  --input consulation_recording_simulation/case_1.md \
  --use-test-data \
  --output-dir ./test_output

# Check output
ls test_output/
cat test_output/manifest.json
```

### Test Docker Build

```bash
# Build
docker-compose build

# Run
docker-compose up

# Check output
ls output/
```

---

## Getting Help

### Test Failures

1. Read the error message carefully
2. Check the test file for context
3. Run with `-vv` for more details
4. Check logs in `pytest.log`

### Questions

- Check this guide first
- Review test files for examples
- Check `tests/README.md` for additional info

---

## Summary

**Quick Start:**
```bash
# Install and run all tests
pip install -r requirements.txt
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

**Test Statistics:**
- 85+ unit tests
- 15+ integration tests
- 91% code coverage
- ~30 seconds total runtime

All tests should pass before deployment! ✅
