# Tool Management Service Tests

This directory contains tests for the Tool Management Service module.

## Test Structure

The tests are organized into the following structure:

- `unit/`: Contains unit tests for individual components
  - `test_tool_interface.py`: Tests for the tool interface classes
  - `test_tool_registry.py`: Tests for the tool registry
  - `test_tool_development_kit.py`: Tests for the tool development kit
  - `test_tool_execution.py`: Tests for the tool execution module

- `integration/`: Contains integration tests
  - `test_tool_management_integration.py`: Tests for the interaction between components

## Running Tests

To run the tests, use pytest:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run a specific test file
pytest tests/unit/test_tool_interface.py

# Run with verbose output
pytest -v
```

## Test Configuration

The test configuration is defined in `pytest.ini`. It includes:

- Test discovery patterns
- Test markers
- Output configuration

## Test Fixtures

Common test fixtures are defined in `conftest.py`. These include:

- `temp_dir`: Creates a temporary directory for testing
- `mock_tool`: Creates a mock tool for testing
- `mock_function_tool`: Creates a mock function tool for testing
- `tool_registry`: Creates a tool registry for testing
- `populated_registry`: Creates a tool registry populated with mock tools
- `tool_validator`: Creates a tool validator for testing
- `tool_packager`: Creates a tool packager for testing
- `tool_executor`: Creates a tool executor for testing
- `mock_registry_with_error`: Creates a mock registry that raises an error
- `mock_tool_with_error`: Creates a mock tool that raises an error

## Adding New Tests

To add a new test:

1. Create a new test file in the appropriate directory (`unit/` or `integration/`)
2. Import the necessary modules and fixtures
3. Define test classes and methods
4. Run the tests to ensure they pass