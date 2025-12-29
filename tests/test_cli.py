"""Tests for OrcaSlicer profile exporter CLI module."""

import json
from pathlib import Path

from click.testing import CliRunner

from src.cli import cli


class TestCLICommandExport:
    """Test CLI export command."""

    def test_export_with_file_path(self, tmp_path: Path) -> None:
        """Test exporting profile with full file path."""
        runner = CliRunner()

        # Create a test profile
        profile_path = tmp_path / "test.json"
        profile_data = {
            "name": "Test Profile",
            "type": "filament",
            "temperature": 200,
        }
        profile_path.write_text(json.dumps(profile_data))

        # Export
        result = runner.invoke(
            cli,
            ["export", str(profile_path), "--output", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "exported" in result.output.lower() or "success" in result.output.lower()

    def test_export_creates_output_directory(self, tmp_path: Path) -> None:
        """Test that export creates output directory if missing."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports" / "nested"

        # Export
        result = runner.invoke(
            cli,
            ["export", str(profile_path), "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        assert output_dir.exists()

    def test_export_with_custom_output_filename(self, tmp_path: Path) -> None:
        """Test export with custom output filename."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        # Export with custom name
        result = runner.invoke(
            cli,
            [
                "export",
                str(profile_path),
                "--output",
                str(output_dir),
                "--output-name",
                "custom.json",
            ],
        )

        assert result.exit_code == 0
        assert (output_dir / "custom.json").exists()

    def test_export_missing_profile_fails(self, tmp_path: Path) -> None:
        """Test that exporting non-existent profile fails."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["export", str(tmp_path / "missing.json")],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_export_with_complex_profile(self, tmp_path: Path) -> None:
        """Test exporting profile with many fields."""
        runner = CliRunner()

        # Create complex profile (no inheritance)
        profile_path = tmp_path / "complex.json"
        profile_data = {
            "name": "Complex Profile",
            "type": "filament",
            "temperature": ["200"],
            "bed_temperature": ["60"],
            "filament_diameter": ["1.75"],
            "filament_density": ["1.25"],
            "compatible_printers": ["Printer1", "Printer2"],
        }
        profile_path.write_text(json.dumps(profile_data))

        # Export
        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        result = runner.invoke(
            cli,
            ["export", str(profile_path), "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        assert (output_dir / "Complex Profile.flattened.json").exists()

        # Verify data was preserved
        exported = json.loads(
            (output_dir / "Complex Profile.flattened.json").read_text()
        )
        assert exported["temperature"] == ["200"]
        assert len(exported["compatible_printers"]) == 2

    def test_export_default_output_directory(self, tmp_path: Path) -> None:
        """Test export with default output directory (current dir)."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        # Export without --output (should use current dir)
        result = runner.invoke(cli, ["export", str(profile_path)])

        # Should succeed (even if we can't verify output location easily)
        assert result.exit_code == 0

    def test_export_validates_profile(self, tmp_path: Path) -> None:
        """Test export with validation enabled."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {
            "name": "Test",
            "type": "filament",
            "temperature": 200,
        }
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        # Export with validation
        result = runner.invoke(
            cli,
            [
                "export",
                str(profile_path),
                "--output",
                str(output_dir),
                "--validate",
            ],
        )

        assert result.exit_code == 0

    def test_export_shows_output_path(self, tmp_path: Path) -> None:
        """Test that export command shows output path."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        # Export
        result = runner.invoke(
            cli,
            ["export", str(profile_path), "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        # Should show the output path
        assert "Test.flattened.json" in result.output or "exports" in result.output


class TestCLIHelp:
    """Test CLI help and information."""

    def test_cli_help(self) -> None:
        """Test main CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "export" in result.output.lower()

    def test_export_help(self) -> None:
        """Test export command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])

        assert result.exit_code == 0
        assert "profile" in result.output.lower()

    def test_cli_version(self) -> None:
        """Test CLI version command if present."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        # Version is optional, so just check it doesn't crash
        assert result.exit_code in (0, 2)


class TestCLIOptions:
    """Test CLI options and flags."""

    def test_output_flag_short(self, tmp_path: Path) -> None:
        """Test short output flag (-o)."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        # Use short flag
        result = runner.invoke(
            cli,
            ["export", str(profile_path), "-o", str(output_dir)],
        )

        assert result.exit_code == 0

    def test_validate_flag(self, tmp_path: Path) -> None:
        """Test validate flag."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        # Use validate flag
        result = runner.invoke(
            cli,
            [
                "export",
                str(profile_path),
                "--output",
                str(output_dir),
                "--validate",
            ],
        )

        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_profile_json(self, tmp_path: Path) -> None:
        """Test export with invalid JSON profile."""
        runner = CliRunner()

        # Create invalid JSON file
        profile_path = tmp_path / "invalid.json"
        profile_path.write_text("{invalid json}")

        result = runner.invoke(cli, ["export", str(profile_path)])

        assert result.exit_code != 0

    def test_profile_without_name_field(self, tmp_path: Path) -> None:
        """Test export with profile missing name field."""
        runner = CliRunner()

        # Create profile without name
        profile_path = tmp_path / "no_name.json"
        profile_data = {"type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        result = runner.invoke(
            cli,
            [
                "export",
                str(profile_path),
                "--output",
                str(output_dir),
                "--validate",
            ],
        )

        # Should fail validation because name is required
        assert result.exit_code != 0

    def test_invalid_output_directory(self, tmp_path: Path) -> None:
        """Test export with invalid output directory."""
        runner = CliRunner()

        # Create test profile
        profile_path = tmp_path / "test.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        # Try to use invalid output directory (parent doesn't exist)
        invalid_output = tmp_path / "nonexistent" / "very" / "nested" / "path"

        result = runner.invoke(
            cli,
            ["export", str(profile_path), "--output", str(invalid_output)],
        )

        # Should succeed because we create directories
        assert result.exit_code == 0


class TestCLIRealWorldScenarios:
    """Test realistic CLI usage scenarios."""

    def test_export_realistic_filament_profile(self, tmp_path: Path) -> None:
        """Test exporting realistic filament profile."""
        runner = CliRunner()

        # Create realistic profile
        profile_path = tmp_path / "filament.json"
        profile_data = {
            "name": "Bambu ABS BBL X1C",
            "type": "filament",
            "temperature": ["245"],
            "bed_temperature": ["80"],
            "filament_id": "BBS",
            "compatible_printers": ["Bambu X1C"],
        }
        profile_path.write_text(json.dumps(profile_data))

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        result = runner.invoke(
            cli,
            ["export", str(profile_path), "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        # Check that a file was created with the profile name
        exported_files = list(output_dir.glob("*.flattened.json"))
        assert len(exported_files) == 1
        assert "Bambu ABS" in exported_files[0].name

    def test_batch_export_simulation(self, tmp_path: Path) -> None:
        """Test exporting multiple profiles sequentially."""
        runner = CliRunner()

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        # Export multiple profiles
        for i in range(3):
            profile_path = tmp_path / f"profile_{i}.json"
            profile_data = {
                "name": f"Profile {i}",
                "type": "filament",
            }
            profile_path.write_text(json.dumps(profile_data))

            result = runner.invoke(
                cli,
                ["export", str(profile_path), "--output", str(output_dir)],
            )

            assert result.exit_code == 0

        # Verify all were exported
        exported_files = list(output_dir.glob("*.json"))
        assert len(exported_files) >= 3


__all__ = [
    "TestCLICommandExport",
    "TestCLIHelp",
    "TestCLIOptions",
    "TestCLIErrorHandling",
    "TestCLIRealWorldScenarios",
]
