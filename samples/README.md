# Sample Configuration Files

This directory contains sample configuration files from OrcaSlicer's official repository.

## Source

All sample files are sourced from:
**https://github.com/OrcaSlicer/OrcaSlicer/tree/main/resources**

## Version Tracking

Sample file versions are tracked through git commits in this repository. Each update from the upstream OrcaSlicer repository should be committed with:

1. A clear commit message indicating the OrcaSlicer version or commit hash
2. Date of the update
3. Any notable changes in the configuration format

### Example Commit Message

```
Update samples from OrcaSlicer v2.0.0

Source: https://github.com/OrcaSlicer/OrcaSlicer/commit/abc123def456
Date: 2025-12-28
Changes: Added new filament profiles for Generic PLA
```

## Directory Structure

### profiles/
Contains manufacturer-specific profiles organized by vendor:
- Filament profiles (*.json)
- Machine profiles (*.json)
- Process profiles (*.json)

These files typically inherit settings from base templates using the `inherits` field.

### profile_templates/
Contains base template files that provide default settings:
- Base filament templates
- Base machine templates
- Base process templates

These are the parent configurations that manufacturer profiles inherit from.

## File Format

OrcaSlicer uses JSON configuration files with inheritance support:

```json
{
  "name": "Profile Name",
  "inherits": "base_template_name",
  "setting_key": "value",
  ...
}
```

The `inherits` field references another profile (usually a template) from which default values are inherited.

## Usage with This Tool

The tools in this repository will:
1. Parse these sample files
2. Resolve inheritance chains
3. Export flattened configurations with all inherited values merged
4. Create self-contained configuration files that work without dependencies
