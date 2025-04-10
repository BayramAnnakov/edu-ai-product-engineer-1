# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test/Lint Commands
- Install: `pip install -r requirements.txt`
- Install AppBot client: `pip install -e ./appbot-client`
- Run tests: `python -m pytest`
- Run specific test: `python -m pytest <test_file>::<test_function>`
- Run AppBot tests: `python appbot-client/run_tests.py`
- CLI usage: `python review_summarizer_cli.py summarize --app-id <id>`
- List apps: `python review_summarizer_cli.py list-apps`
- Code formatting: `black .` and `isort .`
- Linting: `flake8`

## Style Guidelines
- **Imports**: Group imports: stdlib, third-party, local (separated by blank line)
- **Typing**: Use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings with Args/Returns/Raises sections
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use try/except with specific exceptions, avoid bare except
- **Line length**: Max 88 characters
- **String formatting**: Use f-strings for readability
- **CLI design**: Use Typer with proper help text and clear option names
- **Environment**: Use python-dotenv for environment variable management
- **Comments**: Include clear purpose comments in module docstrings