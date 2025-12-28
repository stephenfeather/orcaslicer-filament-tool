"""Tests for OrcaSlicer profile validation module."""

from pathlib import Path

import pytest

from src.validator import CONFLICT_KEYS
from src.validator import OBSOLETE_KEYS
from src.validator import ProfileValidator
from src.validator import ValidationIssue
from src.validator import ValidationResult


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_validation_issue_error(self) -> None:
        """Test creating an error issue."""
        issue = ValidationIssue(level="error", message="Test error")
        assert issue.level == "error"
        assert issue.message == "Test error"
        assert issue.file_path is None

    def test_validation_issue_warning(self) -> None:
        """Test creating a warning issue."""
        issue = ValidationIssue(level="warning", message="Test warning")
        assert issue.level == "warning"
        assert issue.message == "Test warning"

    def test_validation_issue_with_file_path(self, tmp_path: Path) -> None:
        """Test creating an issue with file path."""
        file_path = tmp_path / "test.json"
        issue = ValidationIssue(
            level="error", message="Error in file", file_path=file_path
        )
        assert issue.file_path == file_path


class TestValidationResult:
    """Test ValidationResult dataclass and methods."""

    def test_validation_result_empty(self) -> None:
        """Test creating an empty result."""
        result = ValidationResult()
        assert len(result.issues) == 0
        assert result.files_checked == 0

    def test_validation_result_with_issues(self) -> None:
        """Test creating result with issues."""
        error = ValidationIssue(level="error", message="Error 1")
        warning = ValidationIssue(level="warning", message="Warning 1")
        result = ValidationResult(issues=[error, warning], files_checked=2)

        assert len(result.issues) == 2
        assert result.files_checked == 2

    def test_errors_property(self) -> None:
        """Test filtering errors from result."""
        error1 = ValidationIssue(level="error", message="Error 1")
        error2 = ValidationIssue(level="error", message="Error 2")
        warning = ValidationIssue(level="warning", message="Warning 1")
        result = ValidationResult(issues=[error1, warning, error2])

        assert len(result.errors) == 2
        assert all(i.level == "error" for i in result.errors)

    def test_warnings_property(self) -> None:
        """Test filtering warnings from result."""
        error = ValidationIssue(level="error", message="Error 1")
        warning1 = ValidationIssue(level="warning", message="Warning 1")
        warning2 = ValidationIssue(level="warning", message="Warning 2")
        result = ValidationResult(issues=[warning1, error, warning2])

        assert len(result.warnings) == 2
        assert all(i.level == "warning" for i in result.warnings)

    def test_has_errors_true(self) -> None:
        """Test has_errors when there are errors."""
        error = ValidationIssue(level="error", message="Error")
        result = ValidationResult(issues=[error])
        assert result.has_errors

    def test_has_errors_false(self) -> None:
        """Test has_errors when there are no errors."""
        warning = ValidationIssue(level="warning", message="Warning")
        result = ValidationResult(issues=[warning])
        assert not result.has_errors

    def test_has_errors_empty(self) -> None:
        """Test has_errors on empty result."""
        result = ValidationResult()
        assert not result.has_errors

    def test_error_count(self) -> None:
        """Test error_count property."""
        errors = [ValidationIssue(level="error", message=f"Error {i}") for i in range(3)]
        warnings = [ValidationIssue(level="warning", message=f"Warning {i}") for i in range(2)]
        result = ValidationResult(issues=errors + warnings)

        assert result.error_count == 3

    def test_warning_count(self) -> None:
        """Test warning_count property."""
        errors = [ValidationIssue(level="error", message=f"Error {i}") for i in range(2)]
        warnings = [ValidationIssue(level="warning", message=f"Warning {i}") for i in range(3)]
        result = ValidationResult(issues=errors + warnings)

        assert result.warning_count == 3

    def test_merge_results(self) -> None:
        """Test merging two validation results."""
        result1 = ValidationResult(
            issues=[ValidationIssue(level="error", message="Error 1")],
            files_checked=1,
        )
        result2 = ValidationResult(
            issues=[ValidationIssue(level="warning", message="Warning 1")],
            files_checked=2,
        )

        merged = result1.merge(result2)

        assert len(merged.issues) == 2
        assert merged.files_checked == 3
        assert merged.error_count == 1
        assert merged.warning_count == 1


class TestProfileValidator:
    """Test ProfileValidator class."""

    def test_validator_initialization(self, tmp_path: Path) -> None:
        """Test creating a ProfileValidator."""
        validator = ProfileValidator(profiles_dir=tmp_path)

        assert validator.profiles_dir == tmp_path
        assert validator.obsolete_keys == OBSOLETE_KEYS
        assert validator.conflict_keys == CONFLICT_KEYS

    def test_validator_custom_obsolete_keys(self, tmp_path: Path) -> None:
        """Test validator with custom obsolete keys."""
        custom_keys = {"old_key1", "old_key2"}
        validator = ProfileValidator(profiles_dir=tmp_path, obsolete_keys=custom_keys)

        assert validator.obsolete_keys == custom_keys

    def test_validator_custom_conflict_keys(self, tmp_path: Path) -> None:
        """Test validator with custom conflict keys."""
        custom_conflicts = [["key1", "key2"]]
        validator = ProfileValidator(
            profiles_dir=tmp_path, conflict_keys=custom_conflicts
        )

        assert validator.conflict_keys == custom_conflicts

    def test_validate_filament_compatible_printers_missing(self, tmp_path: Path) -> None:
        """Test validation fails when compatible_printers missing."""
        # Setup directory structure
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        filament_dir = vendor_dir / "filament"
        filament_dir.mkdir(parents=True)

        # Create filament profile with instantiation=true but no compatible_printers
        profile = filament_dir / "test_profile.json"
        profile.write_text('{"name": "Test", "instantiation": "true"}')

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_filament_compatible_printers("TestVendor")

        assert result.has_errors
        assert any("compatible_printers" in i.message for i in result.errors)

    def test_validate_filament_compatible_printers_valid(self, tmp_path: Path) -> None:
        """Test validation passes with compatible_printers."""
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        filament_dir = vendor_dir / "filament"
        filament_dir.mkdir(parents=True)

        # Create filament profile with compatible_printers
        profile = filament_dir / "test_profile.json"
        profile.write_text(
            '{"name": "Test", "instantiation": "true", "compatible_printers": ["Printer1"]}'
        )

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_filament_compatible_printers("TestVendor")

        assert not result.has_errors

    def test_validate_machine_default_materials_missing(self, tmp_path: Path) -> None:
        """Test validation fails when referenced material doesn't exist."""
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        machine_dir = vendor_dir / "machine"
        filament_dir = vendor_dir / "filament"
        machine_dir.mkdir(parents=True)
        filament_dir.mkdir(parents=True)

        # Create machine profile referencing non-existent material
        machine_profile = machine_dir / "test_machine.json"
        machine_profile.write_text(
            '{"name": "TestMachine", "default_materials": ["NonExistent"]}'
        )

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_machine_default_materials("TestVendor")

        assert result.has_errors
        assert any("NonExistent" in i.message for i in result.errors)

    def test_validate_filament_id_valid(self, tmp_path: Path) -> None:
        """Test validation passes with valid filament ID."""
        vendor_dir = tmp_path / "samples" / "profiles" / "BBL"
        filament_dir = vendor_dir / "filament"
        filament_dir.mkdir(parents=True)

        # Create filament profile with valid ID (max 8 chars)
        profile = filament_dir / "test_profile.json"
        profile.write_text('{"name": "Test", "filament_id": "12345678"}')

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_filament_id("BBL")

        assert not result.has_errors

    def test_validate_filament_id_too_long(self, tmp_path: Path) -> None:
        """Test validation fails with ID too long."""
        vendor_dir = tmp_path / "samples" / "profiles" / "OrcaFilamentLibrary"
        filament_dir = vendor_dir / "filament"
        filament_dir.mkdir(parents=True)

        # Create filament profile with ID > 8 chars
        profile = filament_dir / "test_profile.json"
        profile.write_text('{"name": "Test", "filament_id": "123456789"}')

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_filament_id("OrcaFilamentLibrary")

        assert result.has_errors
        assert any("too long" in i.message for i in result.errors)

    def test_validate_obsolete_keys_none(self, tmp_path: Path) -> None:
        """Test validation passes with no obsolete keys."""
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        filament_dir = vendor_dir / "filament"
        filament_dir.mkdir(parents=True)

        # Create filament profile without obsolete keys
        profile = filament_dir / "test_profile.json"
        profile.write_text('{"name": "Test", "nozzle_diameter": 0.4}')

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_obsolete_keys("TestVendor")

        assert not result.has_errors

    def test_validate_obsolete_keys_found(self, tmp_path: Path) -> None:
        """Test validation warns about obsolete keys."""
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        filament_dir = vendor_dir / "filament"
        filament_dir.mkdir(parents=True)

        # Create filament profile with obsolete key
        profile = filament_dir / "test_profile.json"
        profile.write_text('{"name": "Test", "acceleration": 1000}')

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_obsolete_keys("TestVendor")

        assert result.warning_count > 0 or result.error_count > 0

    def test_validate_conflict_keys_none(self, tmp_path: Path) -> None:
        """Test validation passes with no conflicting keys."""
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        machine_dir = vendor_dir / "machine"
        machine_dir.mkdir(parents=True)

        # Create machine profile with only one key from conflict pair
        profile = machine_dir / "test_machine.json"
        profile.write_text(
            '{"name": "TestMachine", "extruder_clearance_radius": 35}'
        )

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_conflict_keys("TestVendor")

        assert not result.has_errors

    def test_validate_conflict_keys_found(self, tmp_path: Path) -> None:
        """Test validation fails with conflicting keys."""
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        machine_dir = vendor_dir / "machine"
        machine_dir.mkdir(parents=True)

        # Create machine profile with both conflicting keys
        profile = machine_dir / "test_machine.json"
        profile.write_text(
            '{"name": "TestMachine", '
            '"extruder_clearance_radius": 35, '
            '"extruder_clearance_max_radius": 35}'
        )

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_conflict_keys("TestVendor")

        assert result.has_errors
        assert any("Conflict" in i.message for i in result.errors)

    def test_validate_all_runs_all_checks(self, tmp_path: Path) -> None:
        """Test validate_all runs multiple validation checks."""
        # Setup minimal structure
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        filament_dir = vendor_dir / "filament"
        machine_dir = vendor_dir / "machine"
        filament_dir.mkdir(parents=True)
        machine_dir.mkdir(parents=True)

        # Create valid profiles
        filament_profile = filament_dir / "test_filament.json"
        filament_profile.write_text('{"name": "TestFilament", "instantiation": "false"}')

        machine_profile = machine_dir / "test_machine.json"
        machine_profile.write_text('{"name": "TestMachine"}')

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")
        result = validator.validate_all("TestVendor")

        # Should return a result even if no errors
        assert isinstance(result, ValidationResult)
        assert result.files_checked > 0

    def test_validate_all_with_checks_disabled(self, tmp_path: Path) -> None:
        """Test validate_all respects check flags."""
        # Setup minimal structure
        vendor_dir = tmp_path / "samples" / "profiles" / "TestVendor"
        vendor_dir.mkdir(parents=True)

        validator = ProfileValidator(profiles_dir=tmp_path / "samples" / "profiles")

        # Run with checks disabled
        result = validator.validate_all(
            "TestVendor",
            check_filaments=False,
            check_materials=False,
            check_obsolete=False,
        )

        assert isinstance(result, ValidationResult)
