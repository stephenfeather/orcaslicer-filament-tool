# OrcaSlicer Filament Tool

Tools and scripts for exporting OrcaSlicer configurations as single-file packages without inheritance dependencies.

## Overview

OrcaSlicer uses an inheritance-based configuration system where filament, machine, and process profiles can inherit settings from parent templates. This tool resolves these inheritance chains and exports fully self-contained configuration files that work independently. Your filament settings should no longer be affected by potential underlying inherited changes.

## Features

- Parse OrcaSlicer configuration files (JSON format)
- Resolve inheritance chains from templates
- Export flattened, self-contained configuration packages
- Support for filament, machine, and process profiles
- **Integrated validation** with comprehensive profile checks
  - Compatible printers verification
  - Filament reference validation
  - Name consistency checking
  - Filament ID constraints
  - Conflict detection for incompatible keys
  - Obsolete key warnings
- Cross-platform support (macOS first, Windows/Linux ready)
- Support for user-created profiles from macOS Application Support directory
- Optional Orca_tools binary validator for additional OrcaSlicer-specific checks

## Usage

Export an OrcaSlicer profile with full inheritance resolution:

```bash
orcaslicer-export "path/to/profile.json" -o ./exports
```

### Examples

**Export a filament profile**:
```bash
orcaslicer-export "/path/to/Fiberon PA6-GF.json" -o ./exports
```

**Export with custom filename**:
```bash
orcaslicer-export "/path/to/profile.json" -o ./exports --output-name my-profile.json
```

**Export with validation**:
```bash
orcaslicer-export "/path/to/profile.json" -o ./exports --validate
```

**Export from macOS Application Support** (example):
```bash
orcaslicer-export ~/Library/Application\ Support/OrcaSlicer/user/*/filament/My\ Profile.json -o ./exports
```

### Output

The exporter creates a flattened JSON file with all inherited settings merged:
- **Filename**: `{profile_name}.flattened.json`
- **Contents**: Complete profile with all parent settings resolved and merged
- **Independence**: The exported profile works without parent template dependencies

### API Usage

```python
from pathlib import Path
from src.config import create_config
from src.resolver import ProfileResolver
from src.exporter import ProfileExporter

# Create config and resolver
config = create_config()
resolver = ProfileResolver(config)

# Resolve profile inheritance
profile_path = Path("/path/to/profile.json")
flattened = resolver.resolve_profile(profile_path)

# Export to JSON
exporter = ProfileExporter(output_dir=Path("./exports"), validate=True)
output_path = exporter.export_profile(flattened, filename="custom.json")
print(f"Exported to: {output_path}")
```

## Development

For information about setting up your development environment, running tests, code style guidelines, and contribution workflows, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Start
- Clone the repository
- Install dependencies: `pip install -r requirements-dev.txt`
- Run tests: `pytest`
- Check code quality: `pylint src/`, `mypy src/`

## Project Structure

```
orcaslicer-filament-tool/
├── samples/
│   ├── profiles/           # Manufacturer-specific profiles (filament, machine, process)
│   └── profile_templates/  # Base templates that other profiles inherit from
├── src/                    # Source code for the tool
└── tests/                  # Test suite
```

## Sample Files

Sample configuration files are sourced from the official OrcaSlicer repository:
- **Source**: https://github.com/OrcaSlicer/OrcaSlicer/tree/main/resources
- **Tracking**: Sample file versions are tracked through git commits in this repository

### profiles/
Contains manufacturer-specific configurations organized by vendor. These files often inherit from base templates.

### profile_templates/
Contains base-level template files that provide default settings inherited by other profiles.

## Resources

For more information about OrcaSlicer profiles and how to create them, see the official documentation:
- [How to create profiles](https://github.com/OrcaSlicer/OrcaSlicer/wiki/How-to-create-profiles) - Official OrcaSlicer wiki guide
- [Validate profiles](https://github.com/OrcaSlicer/OrcaSlicer/wiki/How-to-create-profiles#validate-profiles) - Profile validation guidelines

## License

This project incorporates validation logic derived from the [OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer) project, which is released under the **GNU AFFERO GENERAL PUBLIC LICENSE v3.0 (AGPL-3.0)**.

**Specifically**:
- Validation logic in `src/validator.py` and `orca_extra_profile_check.py` is adapted from OrcaSlicer's profile validation utilities
- Sample profile files in `samples/` are sourced from [OrcaSlicer's official repository](https://github.com/OrcaSlicer/OrcaSlicer/tree/main/resources)

By using this project, you agree to comply with the AGPL-3.0 license terms, which require that:
- Any modifications to this code must be made available under the same AGPL-3.0 license
- Source code must be made available to users of the software

See the [OrcaSlicer License](https://github.com/OrcaSlicer/OrcaSlicer/blob/main/LICENSE) for full details.

For the original OrcaSlicer project, see: https://github.com/OrcaSlicer/OrcaSlicer
