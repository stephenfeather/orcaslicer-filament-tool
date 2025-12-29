"""Profile exporter for OrcaSlicer configurations."""

import json
import re
from pathlib import Path
from typing import Any


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
    ) -> Path:
        """
        Export a single profile to a JSON file.

        Creates output directory if it doesn't exist. If filename is not
        provided, generates one based on profile name.

        Args:
            profile: Profile dictionary to export
            filename: Optional custom filename (without path)

        Returns:
            Absolute path to the exported file

        Raises:
            ExportError: If export fails

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

            # Validate if enabled
            if self.validate:
                self._validate_profile(profile)

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


__all__ = [
    "ExportError",
    "ProfileExporter",
]
