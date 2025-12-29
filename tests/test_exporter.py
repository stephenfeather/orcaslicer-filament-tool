"""Tests for OrcaSlicer profile exporter module."""

import json
from pathlib import Path

import pytest

from src.exporter import ExportError
from src.exporter import ProfileExporter


class TestProfileExporterExceptions:
    """Test custom exception classes."""

    def test_export_error_is_exception(self) -> None:
        """Test ExportError is an Exception."""
        error = ExportError("Test error")
        assert isinstance(error, Exception)


class TestProfileExporterInitialization:
    """Test ProfileExporter initialization."""

    def test_exporter_initialization(self, tmp_path: Path) -> None:
        """Test creating a ProfileExporter."""
        exporter = ProfileExporter(output_dir=tmp_path)
        assert exporter.output_dir == tmp_path

    def test_exporter_default_output_dir(self) -> None:
        """Test exporter with default output directory (current dir)."""
        exporter = ProfileExporter()
        # Should default to current working directory
        assert exporter.output_dir == Path.cwd()

    def test_exporter_with_custom_output_dir(self, tmp_path: Path) -> None:
        """Test exporter with custom output directory."""
        custom_dir = tmp_path / "exports"
        custom_dir.mkdir()
        exporter = ProfileExporter(output_dir=custom_dir)
        assert exporter.output_dir == custom_dir


class TestGenerateFilename:
    """Test ProfileExporter._generate_filename() method."""

    def test_generate_filename_simple(self, tmp_path: Path) -> None:
        """Test generating filename from profile name."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test Profile"}

        filename = exporter._generate_filename(profile)

        assert filename == "Test Profile.flattened.json"

    def test_generate_filename_with_special_chars(self, tmp_path: Path) -> None:
        """Test generating filename with special characters."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test / Profile (v1)"}

        filename = exporter._generate_filename(profile)

        # Special chars like / should be removed or replaced
        assert "flattened.json" in filename
        assert "Test" in filename

    def test_generate_filename_custom_suffix(self, tmp_path: Path) -> None:
        """Test generating filename with custom suffix."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test Profile"}

        filename = exporter._generate_filename(profile, suffix="custom")

        assert filename == "Test Profile.custom.json"

    def test_generate_filename_no_name_field(self, tmp_path: Path) -> None:
        """Test generating filename when profile has no name."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"type": "filament"}  # No name field

        filename = exporter._generate_filename(profile)

        assert "flattened.json" in filename


class TestExportProfile:
    """Test ProfileExporter.export_profile() method."""

    def test_export_simple_profile(self, tmp_path: Path) -> None:
        """Test exporting a simple profile."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test", "type": "filament", "temperature": 200}

        output_path = exporter.export_profile(profile)

        assert output_path.exists()
        assert output_path.parent == tmp_path
        assert "flattened.json" in output_path.name

        # Verify content
        exported = json.loads(output_path.read_text())
        assert exported["name"] == "Test"
        assert exported["temperature"] == 200

    def test_export_profile_to_custom_filename(self, tmp_path: Path) -> None:
        """Test exporting profile with custom filename."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test", "type": "filament"}

        output_path = exporter.export_profile(
            profile, filename="custom_name.json"
        )

        assert output_path.name == "custom_name.json"
        assert output_path.exists()

    def test_export_profile_creates_directory(
        self, tmp_path: Path
    ) -> None:
        """Test that export creates output directory if it doesn't exist."""
        output_dir = tmp_path / "exports" / "nested"
        exporter = ProfileExporter(output_dir=output_dir)
        profile = {"name": "Test", "type": "filament"}

        output_path = exporter.export_profile(profile)

        assert output_dir.exists()
        assert output_path.exists()

    def test_export_profile_with_complex_data(self, tmp_path: Path) -> None:
        """Test exporting profile with complex nested data."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {
            "name": "Complex Profile",
            "type": "filament",
            "temperature": 200,
            "compatible_printers": ["Printer 1", "Printer 2"],
            "settings": {"nested": {"value": 42}},
        }

        output_path = exporter.export_profile(profile)

        exported = json.loads(output_path.read_text())
        assert exported["compatible_printers"] == ["Printer 1", "Printer 2"]
        assert exported["settings"]["nested"]["value"] == 42

    def test_export_profile_preserves_data_types(self, tmp_path: Path) -> None:
        """Test that export preserves data types."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {
            "name": "Test",
            "type": "filament",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "null_value": None,
            "array_value": [1, 2, 3],
        }

        output_path = exporter.export_profile(profile)
        exported = json.loads(output_path.read_text())

        assert exported["int_value"] == 42
        assert exported["float_value"] == 3.14
        assert exported["bool_value"] is True
        assert exported["null_value"] is None
        assert exported["array_value"] == [1, 2, 3]

    def test_export_profile_returns_absolute_path(self, tmp_path: Path) -> None:
        """Test that export returns absolute path."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test", "type": "filament"}

        output_path = exporter.export_profile(profile)

        assert output_path.is_absolute()

    def test_export_overwrites_existing_file(self, tmp_path: Path) -> None:
        """Test that export overwrites existing file."""
        exporter = ProfileExporter(output_dir=tmp_path)
        filename = "test.json"

        # Create initial file
        profile1 = {"name": "Original", "version": 1}
        exporter.export_profile(profile1, filename=filename)

        # Export new profile with same filename
        profile2 = {"name": "Updated", "version": 2}
        output_path = exporter.export_profile(profile2, filename=filename)

        exported = json.loads(output_path.read_text())
        assert exported["name"] == "Updated"
        assert exported["version"] == 2

    def test_export_profile_with_validation(self, tmp_path: Path) -> None:
        """Test exporting profile with validation enabled."""
        exporter = ProfileExporter(output_dir=tmp_path, validate=True)
        profile = {
            "name": "Test",
            "type": "filament",
            "temperature": 200,
        }

        # Should not raise error for valid profile
        output_path = exporter.export_profile(profile)
        assert output_path.exists()

    def test_export_formatting_is_readable(self, tmp_path: Path) -> None:
        """Test that exported JSON is properly formatted (indented)."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {
            "name": "Test",
            "type": "filament",
            "nested": {"key": "value"},
        }

        output_path = exporter.export_profile(profile)
        content = output_path.read_text()

        # Should have indentation (pretty-printed)
        assert "\n" in content
        assert "  " in content or "\t" in content


class TestExportMultipleProfiles:
    """Test exporting multiple profiles."""

    def test_export_multiple_profiles(self, tmp_path: Path) -> None:
        """Test exporting multiple profiles sequentially."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profiles = [
            {"name": "Profile 1", "type": "filament"},
            {"name": "Profile 2", "type": "machine"},
            {"name": "Profile 3", "type": "process"},
        ]

        output_paths = [
            exporter.export_profile(profile) for profile in profiles
        ]

        assert len(output_paths) == 3
        assert all(path.exists() for path in output_paths)
        assert len(set(output_paths)) == 3  # All unique paths

    def test_export_profile_batch(self, tmp_path: Path) -> None:
        """Test batch exporting multiple profiles."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profiles = [
            {"name": f"Profile {i}", "type": "filament"}
            for i in range(5)
        ]

        output_paths = exporter.export_profiles(profiles)

        assert len(output_paths) == 5
        assert all(path.exists() for path in output_paths)

    def test_export_profiles_with_custom_names(
        self, tmp_path: Path
    ) -> None:
        """Test batch exporting with custom filenames."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profiles_with_names = [
            ({"name": "Profile 1", "type": "filament"}, "custom1.json"),
            ({"name": "Profile 2", "type": "filament"}, "custom2.json"),
        ]

        output_paths = [
            exporter.export_profile(profile, filename=name)
            for profile, name in profiles_with_names
        ]

        assert output_paths[0].name == "custom1.json"
        assert output_paths[1].name == "custom2.json"


class TestRealWorldExports:
    """Test exporting realistic profile structures."""

    def test_export_flattened_profile(self, tmp_path: Path) -> None:
        """Test exporting a fully flattened profile with inheritance."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {
            "name": "Fiberon PA6-GF Quidi Q1 Pro (mi3)",
            "type": "filament",
            "from": "User",
            "inherits": "Fiberon PA6-CF @System",
            "temperature": ["300"],
            "bed_temperature": ["50"],
            "filament_id": "OGFL50",
            "compatible_printers": [
                "Qidi Q1 Pro 0.4 nozzle - Klipper",
                "Qidi Q1 Pro 0.6 nozzle - Klipper",
            ],
            "filament_type": ["PA6-CF"],
            "filament_vendor": ["Polymaker"],
        }

        output_path = exporter.export_profile(profile)
        exported = json.loads(output_path.read_text())

        assert exported["name"] == "Fiberon PA6-GF Quidi Q1 Pro (mi3)"
        assert exported["filament_id"] == "OGFL50"
        assert len(exported["compatible_printers"]) == 2

    def test_export_profile_with_many_keys(self, tmp_path: Path) -> None:
        """Test exporting profile with many keys (realistic scenario)."""
        exporter = ProfileExporter(output_dir=tmp_path)

        # Create a profile with 70+ keys (like real profiles)
        profile = {
            "name": "Large Profile",
            "type": "filament",
        }
        for i in range(70):
            profile[f"setting_{i:03d}"] = f"value_{i}"

        output_path = exporter.export_profile(profile)
        exported = json.loads(output_path.read_text())

        # Should have original 72 keys (name + type + 70 settings) plus
        # populated standard filament keys (~56 new keys)
        assert len(exported) >= 72
        # Verify original keys are preserved
        assert exported["setting_000"] == "value_0"
        assert exported["setting_069"] == "value_69"
        # Verify standard keys were populated
        assert "nozzle_temperature" in exported
        assert "filament_density" in exported

    def test_export_maintains_order(self, tmp_path: Path) -> None:
        """Test that export maintains key order (Python 3.7+)."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {
            "z": "last",
            "a": "first",
            "m": "middle",
            "name": "Test",
        }

        output_path = exporter.export_profile(profile)
        exported = json.loads(output_path.read_text())

        # JSON preserves order from dict (Python 3.7+)
        keys = list(exported.keys())
        assert keys[0] == "z"
        assert keys[-1] == "name"  # last key should be "name"

    def test_export_filament_profile_structure(self, tmp_path: Path) -> None:
        """Test exporting filament profile with expected structure."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {
            "name": "Test Filament",
            "type": "filament",
            "temperature": ["200"],
            "bed_temperature": ["60"],
            "filament_diameter": ["1.75"],
            "filament_density": ["1.25"],
            "filament_cost": ["10.00"],
            "compatible_printers": ["Generic Printer"],
        }

        output_path = exporter.export_profile(profile)
        content = output_path.read_text()

        # Verify structure in exported JSON
        assert "Test Filament" in content
        assert "filament" in content
        assert "200" in content


class TestFilenameHandling:
    """Test filename handling and sanitization."""

    def test_sanitize_filename_removes_slashes(self, tmp_path: Path) -> None:
        """Test that slashes are removed from filenames."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Parent/Child Profile"}

        filename = exporter._generate_filename(profile)

        assert "/" not in filename
        assert "flattened.json" in filename

    def test_sanitize_filename_handles_backslashes(
        self, tmp_path: Path
    ) -> None:
        """Test that backslashes are removed from filenames."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Path\\To\\Profile"}

        filename = exporter._generate_filename(profile)

        assert "\\" not in filename

    def test_sanitize_filename_preserves_useful_chars(
        self, tmp_path: Path
    ) -> None:
        """Test that useful characters are preserved."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Profile-v2.0 (Custom)"}

        filename = exporter._generate_filename(profile)

        # These should generally be preserved
        assert "Profile" in filename
        assert "flattened.json" in filename

    def test_export_with_path_traversal_attempt(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are prevented."""
        exporter = ProfileExporter(output_dir=tmp_path)
        profile = {"name": "Test"}

        # Try to use path traversal in filename
        output_path = exporter.export_profile(
            profile, filename="../../../etc/passwd"
        )

        # Should be safely contained in output_dir
        assert output_path.parent == tmp_path


__all__ = [
    "TestProfileExporterExceptions",
    "TestProfileExporterInitialization",
    "TestGenerateFilename",
    "TestExportProfile",
    "TestExportMultipleProfiles",
    "TestRealWorldExports",
    "TestFilenameHandling",
]
