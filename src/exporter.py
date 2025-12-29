"""Profile exporter for OrcaSlicer configurations."""

import json
import re
from pathlib import Path
from typing import Any

from src.constants import DEFAULT_MATERIAL
from src.constants import FILAMENT_MATERIAL_DEFAULTS
from src.constants import STANDARD_FILAMENT_KEYS


class ExportError(Exception):
    """Exception raised during profile export."""


class ProfileExporter:
    """Exports OrcaSlicer profiles to JSON files."""

    def __init__(
        self, output_dir: Path | None = None, validate: bool = False
    ) -> None:
        """
        Initialize ProfileExporter.

        Args:
            output_dir: Directory to export profiles to (default: current dir)
            validate: Whether to validate profiles before exporting

        Examples:
            >>> from pathlib import Path
            >>> exporter = ProfileExporter(output_dir=Path("exports"))
            >>> exported_path = exporter.export_profile(profile)
        """
        self.output_dir = output_dir or Path.cwd()
        self.validate = validate

    def export_profile(
        self,
        profile: dict[str, Any],
        filename: str | None = None,
        source_path: Path | None = None,
    ) -> Path:
        """
        Export a single profile to a JSON file.

        Creates output directory if it doesn't exist. If filename is not
        provided, generates one based on profile name.

        Args:
            profile: Profile dictionary to export
            filename: Optional custom filename (without path)
            source_path: Optional path to source file (used to prevent overwriting)

        Returns:
            Absolute path to the exported file

        Raises:
            ExportError: If export fails or would overwrite source

        Examples:
            >>> profile = {"name": "Test", "type": "filament"}
            >>> exporter = ProfileExporter()
            >>> path = exporter.export_profile(profile)
            >>> print(path)  # exports/Test.flattened.json
        """
        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename if not provided
            if filename is None:
                filename = self._generate_filename(profile)

            # Sanitize filename to prevent path traversal
            filename = self._sanitize_filename(filename)

            # Build full output path
            output_path = self.output_dir / filename

            # Check if output would overwrite source file
            if source_path is not None:
                self._check_source_collision(source_path, output_path)

            # Validate if enabled
            if self.validate:
                self._validate_profile(profile)

            # Populate missing standard keys with material-appropriate defaults
            profile = self._populate_missing_standard_keys(profile)

            # Write JSON to file
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(profile, f, indent=4, ensure_ascii=False)

            return output_path

        except ExportError:
            raise
        except Exception as e:
            raise ExportError(
                f"Failed to export profile '{profile.get('name')}': {e}"
            ) from e

    def export_profiles(
        self, profiles: list[dict[str, Any]]
    ) -> list[Path]:
        """
        Export multiple profiles sequentially.

        Args:
            profiles: List of profile dictionaries to export

        Returns:
            List of absolute paths to exported files

        Examples:
            >>> profiles = [
            ...     {"name": "Profile 1", "type": "filament"},
            ...     {"name": "Profile 2", "type": "filament"},
            ... ]
            >>> exporter = ProfileExporter()
            >>> paths = exporter.export_profiles(profiles)
        """
        return [self.export_profile(profile) for profile in profiles]

    def _get_defaults_for_material(self, filament_type: str) -> dict[str, Any]:
        """
        Get material-appropriate default values for a filament type.

        Uses the filament_type field to lookup template defaults. Falls back to
        PLA defaults for unknown material types.

        Args:
            filament_type: Filament type string (e.g., "PA", "PLA", "PETG", "PA6-CF")

        Returns:
            Dictionary of all 58 standard keys with their default values
        """
        # Clean up filament type string
        material_type = str(filament_type).strip().upper() if filament_type else ""

        # Handle common material names and abbreviations
        # Check these in order of specificity
        if material_type.startswith("PPA"):
            material_type = "PPA-CF"
        elif material_type.startswith("PPS"):
            material_type = "PPS"
        elif material_type.startswith("PA"):  # PA, PA6, PA6-GF, PA6-CF, etc.
            material_type = "PA"
        elif material_type.startswith("PVA"):
            material_type = "PVA"
        elif material_type.startswith("PETG"):
            material_type = "PETG"
        elif material_type.startswith("PLA"):
            material_type = "PLA"
        elif material_type.startswith("TPU"):
            material_type = "TPU"
        elif material_type.startswith("SBS"):
            material_type = "SBS"
        elif material_type.startswith("PC"):
            material_type = "PC"
        elif material_type.startswith("HIPS"):
            material_type = "HIPS"
        elif material_type.startswith("ASA"):
            material_type = "ASA"
        elif material_type.startswith("ABS"):
            material_type = "ABS"

        # Lookup in material defaults, fall back to default if not found
        if material_type in FILAMENT_MATERIAL_DEFAULTS:
            return FILAMENT_MATERIAL_DEFAULTS[material_type].copy()

        return FILAMENT_MATERIAL_DEFAULTS[DEFAULT_MATERIAL].copy()

    def _populate_missing_standard_keys(
        self, profile: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Populate missing standard filament keys with material-appropriate defaults.

        Identifies which standard keys are missing from the profile and adds them
        with defaults matched to the filament's material type. Existing keys are
        never overwritten.

        Args:
            profile: Profile dictionary to populate

        Returns:
            Profile with missing standard keys populated

        Examples:
            >>> profile = {"name": "Test", "type": "filament", "filament_type": ["PA"]}
            >>> exporter = ProfileExporter()
            >>> populated = exporter._populate_missing_standard_keys(profile)
            >>> "nozzle_temperature" in populated  # True
        """
        # Only populate if this is a filament profile
        if profile.get("type") != "filament":
            return profile

        # Extract filament type for material lookup
        filament_type_value = profile.get("filament_type", [DEFAULT_MATERIAL])
        if isinstance(filament_type_value, (list, tuple)):
            filament_type = filament_type_value[0] if filament_type_value else DEFAULT_MATERIAL
        else:
            filament_type = filament_type_value or DEFAULT_MATERIAL

        # Get material-appropriate defaults
        defaults = self._get_defaults_for_material(filament_type)

        # Populate only missing standard keys
        for key in STANDARD_FILAMENT_KEYS:
            if key not in profile and key in defaults:
                profile[key] = defaults[key]

        return profile

    def _generate_filename(
        self, profile: dict[str, Any], suffix: str = "flattened"
    ) -> str:
        """
        Generate filename from profile.

        Uses profile name if available, otherwise generates a default name.
        Adds suffix and .json extension. Sanitizes profile name for safety.

        Args:
            profile: Profile dictionary
            suffix: Suffix before .json extension (default: "flattened")

        Returns:
            Generated filename
        """
        profile_name = profile.get("name", "profile")

        if isinstance(profile_name, (list, tuple)):
            profile_name = profile_name[0] if profile_name else "profile"

        profile_name = str(profile_name).strip()

        # Sanitize profile name to remove invalid characters
        profile_name = profile_name.replace("/", "")
        profile_name = profile_name.replace("\\", "")

        return f"{profile_name}.{suffix}.json"

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and invalid characters.

        Args:
            filename: Original filename
            Returns:
            Sanitized filename

        Examples:
            >>> exporter = ProfileExporter()
            >>> exporter._sanitize_filename("../etc/passwd")
            "etc_passwd"
            >>> exporter._sanitize_filename("valid-filename.json")
            "valid-filename.json"
        """
        # Remove path separators and parent directory references
        filename = filename.replace("../", "")
        filename = filename.replace("..\\", "")
        filename = filename.replace("/", "")
        filename = filename.replace("\\", "")

        # Remove leading dots (hidden files on Unix)
        filename = filename.lstrip(".")

        # Keep only safe characters: alphanumeric, spaces, dash, underscore,
        # dot
        # Allow unicode letters for international filenames
        safe_pattern = r"[^\w\s\-.]"
        filename = re.sub(safe_pattern, "", filename, flags=re.UNICODE)

        # Remove multiple spaces
        filename = re.sub(r"\s+", " ", filename)

        # Ensure filename is not empty
        if not filename:
            filename = "profile"

        return filename

    def _validate_profile(self, profile: dict[str, Any]) -> None:
        """
        Validate profile before export.

        Args:
            profile: Profile to validate

        Raises:
            ExportError: If validation fails
        """
        if not profile:
            raise ExportError("Cannot export empty profile")

        # Check for required fields
        if "name" not in profile:
            raise ExportError("Profile must have a 'name' field")

    def _check_source_collision(self, source_path: Path, output_path: Path) -> None:
        """
        Check if output path would overwrite the source file.

        Compares resolved absolute paths to catch edge cases like symlinks,
        relative paths, or different path representations of the same file.

        Args:
            source_path: Path to source profile file
            output_path: Path to intended output file

        Raises:
            ExportError: If output would overwrite source
        """
        # Resolve to absolute paths to handle symlinks and relative paths
        source_abs = source_path.resolve()
        output_abs = output_path.resolve()

        # Check if they point to the same file
        if source_abs == output_abs:
            raise ExportError(
                f"Cannot overwrite source profile file!\n"
                f"  Source: {source_abs}\n"
                f"  Output would be: {output_abs}\n\n"
                f"Use --output with a different directory or "
                f"--output-name with a different filename."
            )


__all__ = [
    "ExportError",
    "ProfileExporter",
]
