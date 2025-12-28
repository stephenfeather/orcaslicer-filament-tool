# Contributing to OrcaSlicer Filament Tool

This document outlines the ground rules and development practices for this project.

## Table of Contents

1. [Code Style & Standards](#code-style--standards)
2. [Development Workflow](#development-workflow)
3. [Testing Requirements](#testing-requirements)
4. [Dependencies](#dependencies)
5. [File Organization](#file-organization)
6. [Sample File Management](#sample-file-management)
7. [Configuration](#configuration)

## Code Style & Standards

### Python Version
- **Minimum**: Python 3.12
- All code must be compatible with Python 3.12+

### Code Formatting
- **Formatter**: Black (automatic formatting)
- **Line length**: 88 characters (Black default)
- **Import sorting**: isort with Black profile
- Run `black .` and `isort .` before committing (or rely on pre-commit hooks)

### Type Hints
- **Required**: Type hints are mandatory for all function signatures
- **Type checker**: mypy for static type checking
- Type hints protect memory safety, especially important for potential C/Rust compilation

### Docstrings
- **Required**: All public functions, classes, and modules must have docstrings
- **Format**: Google style
- **Example**:
  ```python
  def resolve_inheritance(profile: dict, templates: dict) -> dict:
      """
      Resolve inheritance chain for a profile by merging with parent templates.

      Args:
          profile: The profile configuration to resolve
          templates: Dictionary of available template profiles

      Returns:
          Flattened profile with all inherited values merged

      Raises:
          KeyError: If referenced parent template doesn't exist
      """
      # implementation
  ```

### Linting
- **Linter**: pylint (configured in `.pylintrc`)
- Configuration integrates with VSCode
- Must pass pylint checks before committing

## Development Workflow

### Git Workflow
- **Strategy**: GitHub Flow (feature branches + main)
- **Main branch**: `main` (always deployable)
- **Feature branches**: Create branches for new features/fixes
- **Branch naming**: Descriptive names (e.g., `feature/resolve-inheritance`, `fix/path-detection`)

### Commit Messages
- **Format**: Conventional Commits
- **Structure**: `<type>: <description>`
- **Types**:
  - `feat:` - New feature
  - `fix:` - Bug fix
  - `docs:` - Documentation changes
  - `style:` - Code style changes (formatting, etc.)
  - `refactor:` - Code refactoring
  - `test:` - Adding or updating tests
  - `chore:` - Maintenance tasks

**Examples**:
```
feat: add inheritance resolver for filament profiles
fix: handle missing parent template gracefully
docs: update README with usage examples
test: add unit tests for parser module
```

### Pre-commit Hooks
Pre-commit hooks are configured to run automatically before each commit:
- **black** - Auto-format code
- **isort** - Sort imports
- **pylint** - Lint code
- **mypy** - Type checking
- **trailing-whitespace** - Remove trailing spaces
- **end-of-file-fixer** - Ensure newline at end of files
- **check-json** - Validate JSON syntax
- **check-ast** - Verify Python syntax
- **debug-statements** - Catch forgotten breakpoints

**Setup**:
```bash
pip install -r requirements-dev.txt
pre-commit install
```

## Testing Requirements

### Test-Driven Development (TDD)
- **Required**: Write tests BEFORE implementing features
- Tests must exist before code is considered complete
- Red → Green → Refactor cycle

### Functional Programming
- Prefer functional programming style (easier to test)
- Pure functions where possible
- Minimize side effects

### Coverage
- **Target**: 90% coverage for project code
- Excludes imported modules
- Run: `pytest --cov=src --cov-report=html`

### Test Types
- **Unit tests**: Test individual functions and modules in isolation
- **Integration tests**: Test workflows across multiple modules
  - Example: Full workflow (parse → resolve inheritance → export)
  - Verify modules work together correctly
- Tests located in `tests/` directory
- Mirror source structure: `src/parser.py` → `tests/test_parser.py`
- Integration tests: `tests/test_integration.py`

### Test Requirements
- All features require tests before merging
- Tests must pass before committing
- Coverage must meet 90% threshold

### No CI/CD
- Project size doesn't warrant CI/CD pipeline
- Run tests locally before pushing

## Dependencies

### Philosophy
- **Standard library first**: Always prefer Python standard library when practical
- **Overwhelming value rule**: Only add external dependencies if they provide overwhelming value
- **Minimize dependencies**: Keep external dependencies to an absolute minimum
- **Cross-platform**: Avoid platform-specific libraries
- **Compilation-friendly**: All dependencies must work with Nuitka

### Allowed Dependencies
- Python standard library (strongly preferred)
- External packages only when they provide overwhelming value over standard library alternatives
- Well-maintained, cross-platform packages only
- Must justify any new dependency additions with clear reasoning

### CLI Framework
- **Choice**: `click`
- **Justification**: Provides overwhelming value over `argparse`
  - Clean, functional decorator-based syntax (aligns with functional programming approach)
  - Better user experience with automatic help generation
  - Easier testing of CLI commands
  - More maintainable code with less boilerplate
- Widely used and well-maintained
- Nuitka-compatible
- Minimal dependency footprint (single dependency)

### Adding Dependencies
1. Verify cross-platform compatibility (macOS, Windows, Linux)
2. Check Nuitka compatibility
3. Document reason for dependency
4. Add to `requirements.txt` with version constraint

## File Organization

### Source Structure
```
src/
├── __init__.py         # Package initialization
├── cli.py              # Command-line interface (argparse)
├── config.py           # Configuration handling, path detection
├── parser.py           # Parse OrcaSlicer JSON files
├── resolver.py         # Resolve inheritance chains
├── exporter.py         # Export flattened configs
└── utils.py            # Shared utilities
```

### Test Structure
```
tests/
├── __init__.py
├── test_cli.py
├── test_config.py
├── test_parser.py
├── test_resolver.py
├── test_exporter.py
├── test_utils.py
└── test_integration.py    # Integration tests for cross-module workflows
```

### Module Responsibilities
- **cli.py**: Command-line argument parsing, user interaction
- **config.py**: Detect OrcaSlicer paths, handle configuration
- **parser.py**: Load and parse JSON configuration files
- **resolver.py**: Resolve inheritance chains, merge configurations
- **exporter.py**: Write flattened configurations to files
- **utils.py**: Shared helper functions

## Sample File Management

### Source
- **Upstream**: https://github.com/OrcaSlicer/OrcaSlicer/tree/main/resources
- **Manual updates**: Sample files are updated manually, not automated

### Directory Structure
- `samples/profiles/` - Manufacturer-specific profiles (filament, machine, process)
- `samples/profile_templates/` - Base templates that profiles inherit from

### Version Tracking
- Track OrcaSlicer version in git commit messages
- Include version number and release type (release/dev)

**Commit Message Format**:
```
Add profiles and profile_templates from Orcaslicer 2.3.1 release
Update profiles and profile_templates to Orcaslicer 2.3.2-dev
```

### Update Process
1. Download files from OrcaSlicer repository
2. Update `samples/` directories
3. Commit with descriptive message including version
4. Note any significant changes in commit body

## Configuration

### Platform Support
- **Primary**: macOS (initial development)
- **Future**: Windows, Linux
- **Strategy**: Cross-platform from start, but test on macOS first
- **Goal**: Avoid decisions that complicate multi-platform support

### Tool Type
- **Interface**: Command-line tool
- **Distribution**: Compiled binary (Nuitka)
- **Goal**: Standalone executable, no Python installation required

### Input Methods
Support both:
1. **Filename only**: Auto-detect OrcaSlicer config directory
   ```bash
   orcaslicer-export "Generic PLA.json"
   ```
2. **Full path**: Explicit file path
   ```bash
   orcaslicer-export /path/to/filament.json
   ```

### OrcaSlicer Directory Detection
- **Auto-detect**: Search common OrcaSlicer config locations
- **Override**: `--config-dir` flag for manual specification
- **macOS default**: `~/Library/Application Support/OrcaSlicer/`

### Output
- **Default location**: Current working directory
- **Override**: `--output` flag to specify directory
- **Filename format**: `{original_name}.flattened.json`
  - Input: `Generic PLA.json`
  - Output: `Generic PLA.flattened.json`
- **Profile name**: Name inside JSON determines how it appears in OrcaSlicer

### Binary Compilation
- **Tool**: Nuitka
- **Target**: Native executable for each platform
- **Benefits**:
  - No Python interpreter required
  - Faster startup
  - Easier distribution for users

## Development Setup

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd orcaslicer-filament-tool

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality Checks
```bash
# Format code
black .
isort .

# Type checking
mypy src/

# Linting
pylint src/
```

### Profile Validation

Profile validation is performed using the **Orca_tools validator**, which is available as a compiled binary from the official release:
- **Download**: https://github.com/SoftFever/Orca_tools/releases/tag/1
- **Purpose**: Validates OrcaSlicer profile JSON files for correctness and compatibility

#### Installation
Download the appropriate binary for your platform from the Orca_tools releases page and place it in your system PATH or a known location.

#### Usage
Before committing profile changes or sample files, validate them with the Orca_tools validator:
```bash
# Validate a single profile
orca_tools validate-profile path/to/profile.json

# Validate all sample profiles
orca_tools validate-profile samples/profiles/**/*.json
```

### Manual Pre-commit Check
```bash
# Run all pre-commit hooks manually
pre-commit run --all-files
```
