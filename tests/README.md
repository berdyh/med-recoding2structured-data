# Test Suite

This directory contains unit tests and integration tests for the GP Consultation Data Extraction System.

## Testing Strategy

### Unit Tests

Unit tests focus on individual components in isolation, using mocks for external dependencies.

**Test Files**:
- `test_input_handler.py`: Tests for file reading and validation
- `test_llm_provider.py`: Tests for provider selection and credential validation
- `test_entity_extractor.py`: Tests for entity extraction with mocked LLM responses
- `test_data_mapper.py`: Tests for schema mapping and UUID generation
- `test_csv_exporter.py`: Tests for CSV generation and manifest creation
- `test_validator.py`: Tests for validation rules
- `test_test_data_generator.py`: Tests for test data generation

**Mocking Strategy**:
- Mock LangExtract API calls to avoid real API usage
- Mock file I/O operations for predictable test behavior
- Mock environment variables for configuration testing

### Integration Tests

Integration tests validate the complete pipeline from input to output.

**Test File**: `test_integration.py`

**Test Scenarios**:
1. End-to-end extraction with `case_1.md` (lower back pain)
2. End-to-end extraction with `case_2.md` (sore throat)
3. Empty consultation handling (no entities extracted)
4. Malformed input handling
5. API failure and retry logic
6. Test data generation with `--use-test-data` flag

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_input_handler.py
```

### Run with Verbose Output
```bash
pytest -v tests/
```

### Run with Coverage Report
```bash
pytest --cov=src --cov-report=html tests/
```

### Run Integration Tests Only
```bash
pytest tests/test_integration.py
```

### Run Unit Tests Only
```bash
pytest tests/ --ignore=tests/test_integration.py
```

## Test Data Requirements

### Sample Consultation Files

Integration tests use consultation files from `consulation_recording_simulation/`:
- `case_1.md`: Lower back pain (mechanical strain)
- `case_2.md`: Sore throat (bacterial tonsillitis)
- `case_3.md`: Additional test case
- `case_4.md`: Additional test case

### Mock Data

Unit tests use mock data defined in test files:
- Mock LLM responses with sample entity extractions
- Mock configuration dictionaries
- Mock file content strings

## Test Fixtures

Common fixtures are defined in `conftest.py`:
```python
@pytest.fixture
def sample_transcript():
    """Sample consultation transcript for testing"""
    return "Patient: I have a headache..."

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider manager"""
    return Mock(spec=LLMProviderManager)
```

## Writing New Tests

### Unit Test Template
```python
import pytest
from src.module_name import ClassName

def test_method_name():
    """Test description"""
    # Arrange
    instance = ClassName()
    
    # Act
    result = instance.method()
    
    # Assert
    assert result == expected_value
```

### Integration Test Template
```python
import pytest
from src.main import main

def test_end_to_end_extraction(tmp_path):
    """Test complete extraction pipeline"""
    # Arrange
    input_file = "consulation_recording_simulation/case_1.md"
    output_dir = tmp_path / "output"
    
    # Act
    exit_code = main(["--input", input_file, "--output", str(output_dir)])
    
    # Assert
    assert exit_code == 0
    assert (output_dir / "symptoms.csv").exists()
```

## Continuous Integration

Tests should be run automatically on:
- Every commit
- Every pull request
- Before deployment

## Test Coverage Goals

- **Unit Tests**: >80% code coverage
- **Integration Tests**: Cover all major user workflows
- **Critical Paths**: 100% coverage for data mapping and validation

## Troubleshooting

### Tests Fail Due to Missing API Keys
- Unit tests should not require real API keys (use mocks)
- Integration tests may require API keys in environment variables

### Tests Fail Due to Missing Files
- Ensure consultation files exist in `consulation_recording_simulation/`
- Check that test data files are not in `.gitignore`

### Slow Test Execution
- Use mocks for external API calls
- Consider marking slow tests with `@pytest.mark.slow`
- Run fast tests during development, full suite in CI

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Mock External Dependencies**: Don't rely on external services
4. **Test Edge Cases**: Include tests for error conditions
5. **Keep Tests Fast**: Unit tests should run in milliseconds
6. **Descriptive Names**: Test names should describe what they test
