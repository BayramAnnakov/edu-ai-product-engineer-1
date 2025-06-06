# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Run all tests: `python -m pytest`
- Run a single test: `python -m pytest tests/test_file.py::TestClass::test_method -v`
- Run appbot client tests: `python run_tests.py`
- Run specific userboard tests: `python -m pytest userboard/tests/test_utils.py::test_function`
- Linting: `black . && ruff check .`

## Code Style Guidelines
- **Imports**: Group imports: standard lib, third-party, local imports
- **Typing**: Use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings with args/returns sections
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use specific exception types with informative messages
- **Testing**: Write unit tests with pytest and use mock for external dependencies
- **Formatting**: Use black for code formatting and ruff for linting
- **API Clients**: Constructor should accept auth via args or environment variables
- **File organization**: Use src/ for source code, tests/ for unit tests