# OrcaSlicer Filament Tool

Tools and scripts for exporting OrcaSlicer configurations as single-file packages without inheritance dependencies.

## Overview

OrcaSlicer uses an inheritance-based configuration system where filament, machine, and process profiles can inherit settings from parent templates. This tool resolves these inheritance chains and exports fully self-contained configuration files that work independently.

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

## References

For more information about OrcaSlicer profiles and how to create them, see the official documentation:
- [How to create profiles](https://github.com/OrcaSlicer/OrcaSlicer/wiki/How-to-create-profiles) - Official OrcaSlicer wiki guide
- [Validate profiles](https://github.com/OrcaSlicer/OrcaSlicer/wiki/How-to-create-profiles#validate-profiles) - Profile validation guidelines

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

(Coming soon)

## Development

(Coming soon)

## License

(Coming soon)
