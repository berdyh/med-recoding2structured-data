# Testing Documentation

This directory contains the test suite for the GP Consultation Data Extraction System.

## Testing Strategy

The test suite includes:

1. **Unit Tests**: Test individual modules in isolation
2. **Integration Tests**: Test end-to-end extraction pipeline
3. **Mock Tests**: Mock external dependencies (LLM APIs, file I/O)

## Test Structure

```
tests/
├── README.md                      # This file
├── test_config_manager.py         # Configuration tests
├── test_llm_provider.py           # LLM provider tests
├── test_input_handler.py          # Input handling tests
├── test_entity_extractor.py       # Entity extraction tests (optional)
├── test_data_mapper.py            # Data mapping tests (optional)
├── test_validator.py              # Validation tests
├── test_csv_exporter.py           # CSV export tests (optional)
├── test_test_data_generator.py    # Test data generation tests
└── test_integration.py            # End-to-end integration tests (optional)
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_config_manager.py
```

### Run Specific Test Function

```bash
pytest tests/test_config_manager.py::test_load_config
```

### Run with Coverage

```bash
pytest --cov=src tests/
```

### Run with Verbose Output

```bash
pytest -v tests/
```

### Run Integration Tests Only

```bash
pytest tests/test_integration.py
```

## Test Requirements

### Dependencies

Install test dependencies:
```bash
pip install pytest pytest-mock pytest-cov
```

### Test Data

Test data files are located in:
- `input/case_1.md`: Lower back pain consultation
- `input/case_2.md`: Sore throat consultation

### Environment Variables

For integration tests, set:
```bash
export LANGEXTRACT_API_KEY="your-test-api-key"
```

Or use mock mode (no API calls):
```bash
export MOCK_LLM_CALLS=true
```

## Unit Tests

### test_config_manager.py

Tests configuration loading and validation:
- Load from YAML file
- Override with environment variables
- Validate required fields
- Handle missing configuration

**Example:**
```python
def test_load_config():
    config = ConfigManager('config/config.yaml')
    assert config.get('llm.provider') in ['gemini', 'bedrock']
```

### test_llm_provider.py

Tests LLM provider selection and credentials:
- Provider selection based on environment
- Credential validation
- Error handling for missing credentials
- Bedrock client initialization

**Example:**
```python
def test_provider_selection(monkeypatch):
    monkeypatch.setenv('LANGEXTRACT_API_KEY', 'test-key')
    provider = LLMProviderManager(config)
    assert provider.get_provider() == 'gemini'
```

### test_input_handler.py

Tests input file reading and validation:
- Read Markdown files
- Handle file not found errors
- Validate file format
- Handle encoding errors

**Example:**
```python
def test_read_transcript():
    handler = InputHandler()
    transcript = handler.read_transcript('input/case_1.md')
    assert len(transcript) > 0
    assert 'Patient' in transcript or 'GP' in transcript
```

### test_validator.py

Tests data validation rules:
- Severity validation
- Certainty validation
- Dosage validation
- Date validation
- NHS number validation

**Example:**
```python
def test_validate_severity():
    validator = Validator()
    assert validator.validate_severity('moderate') == True
    assert validator.validate_severity('invalid') == False
```

### test_test_data_generator.py

Tests test data generation:
- Patient data generation
- Doctor data generation
- NHS number generation and validation
- UUID consistency

**Example:**
```python
def test_generate_patient():
    generator = TestDataGenerator()
    patient = generator.generate_patient()
    assert 'patient_id' in patient
    assert 'nhs_number' in patient
    assert len(patient['nhs_number']) == 10
```

## Integration Tests (Optional)

### test_integration.py

Tests end-to-end extraction pipeline:
- Extract from case_1.md
- Extract from case_2.md
- Verify CSV outputs
- Verify manifest file
- Test with --use-test-data flag

**Example:**
```python
def test_end_to_end_extraction():
    # Run extraction
    result = subprocess.run([
        'python', '-m', 'src.main',
        '--input', 'input/case_1.md',
        '--use-test-data',
        '--output-dir', 'test_output'
    ], capture_output=True)
    
    assert result.returncode == 0
    assert os.path.exists('test_output/symptoms.csv')
    assert os.path.exists('test_output/manifest.json')
```

## Mocking

### Mock LangExtract API Calls

```python
from unittest.mock import Mock, patch

@patch('langextract.extract')
def test_extract_symptoms(mock_extract):
    # Mock LangExtract response
    mock_result = Mock()
    mock_result.extractions = [
        Mock(extraction_class='symptom_name', extraction_text='headache', attributes={})
    ]
    mock_extract.return_value = mock_result
    
    # Test extraction
    extractor = ClinicalEntityExtractor(llm_provider)
    symptoms = extractor.extract_symptoms("Patient has headache")
    
    assert len(symptoms) > 0
    assert symptoms[0]['class'] == 'symptom_name'
```

### Mock File I/O

```python
from unittest.mock import mock_open, patch

@patch('builtins.open', mock_open(read_data='# Test Consultation\n\n**Patient**: Test'))
def test_read_transcript():
    handler = InputHandler()
    transcript = handler.read_transcript('test.md')
    assert 'Test Consultation' in transcript
```

## Test Coverage

Target coverage: >80% for core modules

Check coverage:
```bash
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html
```

## Test Data Requirements

### Minimal Test Consultation

```markdown
# GP Consultation

**Patient**: I have a headache.

**GP**: How long have you had this headache?

**Patient**: Since yesterday.
```

### Complete Test Consultation

Use provided case files:
- `input/case_1.md`: Comprehensive lower back pain case
- `input/case_2.md`: Comprehensive sore throat case

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
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=src
```

## Debugging Tests

### Run with Debug Output

```bash
pytest -vv -s tests/test_config_manager.py
```

### Run with PDB on Failure

```bash
pytest --pdb tests/
```

### Run Specific Test with Print Statements

```bash
pytest -s tests/test_input_handler.py::test_read_transcript
```

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies (APIs, file I/O)
3. **Assertions**: Use clear, specific assertions
4. **Cleanup**: Clean up test files and resources
5. **Documentation**: Document test purpose and expected behavior

## Common Test Patterns

### Setup and Teardown

```python
import pytest

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    yield output_dir
    # Cleanup happens automatically

def test_csv_export(temp_output_dir):
    exporter = CSVExporter(str(temp_output_dir))
    # Test export
```

### Parametrized Tests

```python
@pytest.mark.parametrize("severity,expected", [
    ("mild", True),
    ("moderate", True),
    ("severe", True),
    ("invalid", False),
])
def test_validate_severity(severity, expected):
    validator = Validator()
    assert validator.validate_severity(severity) == expected
```

### Exception Testing

```python
def test_missing_file():
    handler = InputHandler()
    with pytest.raises(FileNotFoundError):
        handler.read_transcript('nonexistent.md')
```

## Performance Testing

### Test Processing Time

```python
import time

def test_extraction_performance():
    start = time.time()
    # Run extraction
    duration = time.time() - start
    assert duration < 60  # Should complete in <60 seconds
```

## Test Maintenance

- Update tests when adding new features
- Remove obsolete tests
- Keep test data up to date
- Review test coverage regularly
- Fix flaky tests immediately

## Troubleshooting

### Tests Fail with API Errors

- Check API key is set: `echo $LANGEXTRACT_API_KEY`
- Use mock mode: `export MOCK_LLM_CALLS=true`
- Check network connectivity

### Tests Fail with Import Errors

- Verify dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.12+)

### Tests Fail with File Not Found

- Verify test data exists: `ls input/case_*.md`
- Check working directory: `pwd`

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
