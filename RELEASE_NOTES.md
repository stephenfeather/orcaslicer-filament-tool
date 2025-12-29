# OrcaSlicer Filament Tool v0.1.0

## Initial Release

The OrcaSlicer Filament Tool provides a streamlined way to export OrcaSlicer configuration profiles as fully self-contained JSON packages. This eliminates inheritance dependencies, allowing your filament, machine, and process profiles to work independently without relying on parent template changes.

## Core Features

**Profile Export & Flattening** - Export any OrcaSlicer profile with all inherited settings automatically resolved and merged into a single file. Supports filament, machine, and process profile types with automatic type detection from directory structure.

**Comprehensive Validation** - Built-in validation checks compatible printers, filament references, naming consistency, filament ID constraints, and detects conflicts between incompatible keys. Optional integration with OrcaSlicer's `orca_tools` binary for additional checks.

**Command-Line Interface** - Simple CLI tool for exporting profiles with custom output naming and optional validation. Includes support for user-created profiles from macOS Application Support directory.

**Python API** - Programmatic access for integration into other tools. Clean separation of concerns across dedicated modules for parsing, resolving, validation, and export.

## What's Included

- Full inheritance resolution engine for flattening complex profile chains
- Extensible validation framework adapted from OrcaSlicer's validation utilities
- Comprehensive test suite with code quality tooling (pylint, mypy)
- Sample profiles from OrcaSlicer 2.3.1 for testing and reference

## Getting Started

```bash
# Basic export
orcaslicer-export "/path/to/profile.json" -o ./exports

# Export with validation
orcaslicer-export "/path/to/profile.json" -o ./exports --validate

# Custom output filename
orcaslicer-export "/path/to/profile.json" -o ./exports --output-name my-profile.json
```

See [README.md](README.md) for detailed usage examples and API documentation.

## License

This project incorporates validation logic derived from OrcaSlicer, released under AGPL-3.0. By using this project, you agree to comply with AGPL-3.0 license terms.
