"""Profile validation module for OrcaSlicer configurations."""

import json
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Literal
from typing import Optional

# Constants
OBSOLETE_KEYS: set[str] = {
    "acceleration",
    "scale",
    "rotate",
    "duplicate",
    "duplicate_grid",
    "bed_size",
    "print_center",
    "g0",
    "wipe_tower_per_color_wipe",
    "support_sharp_tails",
    "support_remove_small_overhangs",
    "support_with_sheath",
    "tree_support_collision_resolution",
    "tree_support_with_infill",
    "max_volumetric_speed",
    "max_print_speed",
    "support_closing_radius",
    "remove_freq_sweep",
    "remove_bed_leveling",
    "remove_extrusion_calibration",
    "support_transition_line_width",
    "support_transition_speed",
    "bed_temperature",
    "bed_temperature_initial_layer",
    "can_switch_nozzle_type",
    "can_add_auxiliary_fan",
    "extra_flush_volume",
    "spaghetti_detector",
    "adaptive_layer_height",
    "z_hop_type",
    "z_lift_type",
    "bed_temperature_difference",
    "long_retraction_when_cut",
    "retraction_distance_when_cut",
    "extruder_type",
    "internal_bridge_support_thickness",
    "extruder_clearance_max_radius",
    "top_area_threshold",
    "reduce_wall_solid_infill",
    "filament_load_time",
    "filament_unload_time",
    "smooth_coefficient",
    "overhang_totally_speed",
    "silent_mode",
    "overhang_speed_classic",
}

CONFLICT_KEYS: list[list[str]] = [
    ["extruder_clearance_radius", "extruder_clearance_max_radius"],
]


@dataclass
class ValidationIssue:
    """Single validation issue."""

    level: Literal["error", "warning"]
    message: str
    file_path: Optional[Path] = None


@dataclass
class ValidationResult:
    """Result of validation run."""

    issues: list[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get all error issues."""
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get all warning issues."""
        return [i for i in self.issues if i.level == "warning"]

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def error_count(self) -> int:
        """Get count of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get count of warnings."""
        return len(self.warnings)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """
        Merge two validation results.

        Args:
            other: Another ValidationResult to merge

        Returns:
            New ValidationResult with combined issues and files checked
        """
        return ValidationResult(
            issues=self.issues + other.issues,
            files_checked=self.files_checked + other.files_checked,
        )


def load_json_with_duplicate_check(file_path: Path) -> dict:  # type: ignore
    """
    Load JSON file and check for duplicate keys.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If duplicate keys are found
        json.JSONDecodeError: If JSON is invalid
    """

    def no_duplicates_hook(pairs):  # type: ignore
        """Hook to detect duplicate keys during JSON parsing."""
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError(f"Duplicate key detected: {key}")
            seen[key] = value
        return seen

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=no_duplicates_hook)


def load_available_filament_profiles(profiles_dir: Path, vendor_name: str) -> set[str]:
    """
    Load all available filament profile names from a vendor.

    Args:
        profiles_dir: Base profiles directory
        vendor_name: Vendor name to check

    Returns:
        Set of filament profile names
    """
    profiles: set[str] = set()
    vendor_path = profiles_dir / vendor_name / "filament"

    if not vendor_path.exists():
        return profiles

    for file_path in vendor_path.rglob("*.json"):
        try:
            with file_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
                if "name" in data:
                    profiles.add(data["name"])
        except Exception:
            pass

    return profiles


class ProfileValidator:
    """Validates OrcaSlicer profiles."""

    def __init__(
        self,
        profiles_dir: Path,
        obsolete_keys: set[str] | None = None,
        conflict_keys: list[list[str]] | None = None,
    ) -> None:
        """
        Initialize ProfileValidator.

        Args:
            profiles_dir: Base profiles directory
            obsolete_keys: Set of obsolete key names to check (default: OBSOLETE_KEYS)
            conflict_keys: List of conflicting key pairs (default: CONFLICT_KEYS)
        """
        self.profiles_dir = profiles_dir
        self.obsolete_keys = obsolete_keys or OBSOLETE_KEYS
        self.conflict_keys = conflict_keys or CONFLICT_KEYS

    def validate_filament_compatible_printers(
        self, vendor_name: str
    ) -> ValidationResult:
        """
        Validate compatible_printers in filament profiles.

        Args:
            vendor_name: Vendor name to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        vendor_path = self.profiles_dir / vendor_name / "filament"

        if not vendor_path.exists():
            return result

        profiles = {}

        # Load all profiles
        for file_path in vendor_path.rglob("*.json"):
            if file_path.name == "filaments_color_codes.json":
                continue

            try:
                data = load_json_with_duplicate_check(file_path)
            except Exception as e:
                result.issues.append(
                    ValidationIssue(
                        level="error",
                        message=f"Error loading {file_path.name}: {e}",
                        file_path=file_path,
                    )
                )
                continue

            profile_name = data.get("name")
            if not profile_name:
                continue

            if profile_name in profiles:
                result.issues.append(
                    ValidationIssue(
                        level="error",
                        message=f"Duplicate profile: {profile_name}",
                        file_path=file_path,
                    )
                )
                continue

            profiles[profile_name] = {"file_path": file_path, "content": data}

        result.files_checked = len(profiles)

        # Helper functions for inheritance resolution
        def get_property(profile, key):  # type: ignore
            """Get property from profile."""
            content = profile["content"]
            if key in content:
                return content[key]
            return None

        def get_inherit_property(profile, key):  # type: ignore
            """Get property with inheritance resolution."""
            content = profile["content"]
            if key in content:
                return content[key]

            if "inherits" in content:
                inherits = content["inherits"]
                if inherits not in profiles:
                    raise ValueError(f"Parent profile not found: {inherits}")
                return get_inherit_property(profiles[inherits], key)

            return None

        # Validate each profile
        for profile in profiles.values():
            profile_file_path: Path = profile["file_path"]  # type: ignore
            profile_content: dict = profile["content"]  # type: ignore
            instantiation = str(profile_content.get("instantiation", "")).lower() == "true"
            if instantiation:
                try:
                    compatible_printers = get_property(profile, "compatible_printers")
                    if not compatible_printers or (
                        isinstance(compatible_printers, list) and not compatible_printers
                    ):
                        result.issues.append(
                            ValidationIssue(
                                level="error",
                                message=f"Missing compatible_printers in {profile_file_path.name}",
                                file_path=profile_file_path,
                            )
                        )
                except ValueError as e:
                    result.issues.append(
                        ValidationIssue(
                            level="error",
                            message=f"Error parsing {profile_file_path.name}: {e}",
                            file_path=profile_file_path,
                        )
                    )

        return result

    def validate_machine_default_materials(self, vendor_name: str) -> ValidationResult:
        """
        Validate machine default material references.

        Args:
            vendor_name: Vendor name to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        machine_dir = self.profiles_dir / vendor_name / "machine"

        if not machine_dir.exists():
            return result

        # Load available filaments
        vendor_filaments = load_available_filament_profiles(self.profiles_dir, vendor_name)
        global_filaments = load_available_filament_profiles(
            self.profiles_dir, "OrcaFilamentLibrary"
        )
        all_available = vendor_filaments.union(global_filaments)

        # Check each machine profile
        for file_path in machine_dir.rglob("*.json"):
            try:
                with file_path.open("r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                continue

            result.files_checked += 1

            default_materials = None
            if "default_materials" in data:
                default_materials = data["default_materials"]
            elif "default_filament_profile" in data:
                default_materials = data["default_filament_profile"]

            if default_materials:
                if isinstance(default_materials, list):
                    for material in default_materials:
                        if material not in all_available:
                            result.issues.append(
                                ValidationIssue(
                                    level="error",
                                    message=f"Missing filament: {material}",
                                    file_path=file_path,
                                )
                            )
                else:
                    # Handle semicolon-separated string
                    materials_list = [
                        m.strip()
                        for m in default_materials.split(";")
                        if m.strip()
                    ]
                    for material in materials_list:
                        if material not in all_available:
                            result.issues.append(
                                ValidationIssue(
                                    level="error",
                                    message=f"Missing filament: {material}",
                                    file_path=file_path,
                                )
                            )

        return result

    def validate_name_consistency(self, vendor_name: str) -> ValidationResult:
        """
        Validate name consistency between vendor index and profile files.

        Args:
            vendor_name: Vendor name to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        vendor_dir = self.profiles_dir / vendor_name
        vendor_file = self.profiles_dir / f"{vendor_name}.json"

        if not vendor_file.exists():
            return result

        try:
            with vendor_file.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            result.issues.append(
                ValidationIssue(
                    level="error",
                    message=f"Error loading vendor file: {e}",
                    file_path=vendor_file,
                )
            )
            return result

        for section in ["filament_list", "machine_model_list", "machine_list", "process_list"]:
            if section not in data:
                continue

            for child in data[section]:
                name_in_vendor = child["name"]
                sub_path = child["sub_path"]
                sub_file = vendor_dir / sub_path

                if not sub_file.exists():
                    result.issues.append(
                        ValidationIssue(
                            level="error",
                            message=f"Missing sub_path: {sub_path}",
                            file_path=vendor_file,
                        )
                    )
                    continue

                try:
                    with sub_file.open("r", encoding="utf-8") as fp:
                        sub_data = json.load(fp)
                except Exception as e:
                    result.issues.append(
                        ValidationIssue(
                            level="error",
                            message=f"Error loading {sub_path}: {e}",
                            file_path=sub_file,
                        )
                    )
                    continue

                name_in_sub = sub_data.get("name")
                if name_in_sub != name_in_vendor:
                    result.issues.append(
                        ValidationIssue(
                            level="error",
                            message=f"Name mismatch: {name_in_vendor} != {name_in_sub}",
                            file_path=sub_file,
                        )
                    )

                result.files_checked += 1

        return result

    def validate_filament_id(self, vendor_name: str) -> ValidationResult:
        """
        Validate filament ID length constraints.

        Args:
            vendor_name: Vendor name to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        # Only check for specific vendors
        if vendor_name not in ("BBL", "OrcaFilamentLibrary"):
            return result

        vendor_path = self.profiles_dir / vendor_name / "filament"

        if not vendor_path.exists():
            return result

        for file_path in vendor_path.rglob("*.json"):
            try:
                data = load_json_with_duplicate_check(file_path)
            except Exception:
                continue

            result.files_checked += 1

            if "filament_id" in data:
                filament_id = data["filament_id"]
                if len(filament_id) > 8:
                    result.issues.append(
                        ValidationIssue(
                            level="error",
                            message=f"Filament ID too long (max 8): {filament_id}",
                            file_path=file_path,
                        )
                    )

        return result

    def validate_obsolete_keys(self, vendor_name: str) -> ValidationResult:
        """
        Check for obsolete keys in filament profiles.

        Args:
            vendor_name: Vendor name to validate

        Returns:
            ValidationResult with any warnings found
        """
        result = ValidationResult()
        vendor_path = self.profiles_dir / vendor_name / "filament"

        if not vendor_path.exists():
            return result

        for file_path in vendor_path.rglob("*.json"):
            try:
                with file_path.open("r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                continue

            result.files_checked += 1

            for key in data.keys():
                if key in self.obsolete_keys:
                    result.issues.append(
                        ValidationIssue(
                            level="warning",
                            message=f"Obsolete key '{key}' in {file_path.name}",
                            file_path=file_path,
                        )
                    )

        return result

    def validate_conflict_keys(self, vendor_name: str) -> ValidationResult:
        """
        Check for conflicting keys in profiles.

        Args:
            vendor_name: Vendor name to validate

        Returns:
            ValidationResult with any errors found
        """
        result = ValidationResult()
        vendor_path = self.profiles_dir / vendor_name

        if not vendor_path.exists():
            return result

        for file_path in vendor_path.rglob("*.json"):
            try:
                data = load_json_with_duplicate_check(file_path)
            except Exception:
                continue

            result.files_checked += 1

            for key_set in self.conflict_keys:
                found_count = sum(1 for k in key_set if k in data)
                if found_count > 1:
                    result.issues.append(
                        ValidationIssue(
                            level="error",
                            message=f"Conflict keys {key_set} co-exist in {file_path.name}",
                            file_path=file_path,
                        )
                    )

        return result

    def validate_all(
        self,
        vendor_name: str,
        check_filaments: bool = True,
        check_materials: bool = True,
        check_obsolete: bool = False,
    ) -> ValidationResult:
        """
        Run all validations and combine results.

        Args:
            vendor_name: Vendor name to validate
            check_filaments: Whether to check filament compatible_printers
            check_materials: Whether to check machine default materials
            check_obsolete: Whether to check for obsolete keys

        Returns:
            Combined ValidationResult from all checks
        """
        results: list[ValidationResult] = []

        if check_filaments:
            results.append(self.validate_filament_compatible_printers(vendor_name))

        if check_materials:
            results.append(self.validate_machine_default_materials(vendor_name))

        # Always run these
        results.append(self.validate_name_consistency(vendor_name))
        results.append(self.validate_conflict_keys(vendor_name))
        results.append(self.validate_filament_id(vendor_name))

        if check_obsolete:
            results.append(self.validate_obsolete_keys(vendor_name))

        # Merge all results
        merged = ValidationResult()
        for result in results:
            merged = merged.merge(result)

        return merged


__all__ = [
    "OBSOLETE_KEYS",
    "CONFLICT_KEYS",
    "ValidationIssue",
    "ValidationResult",
    "ProfileValidator",
    "load_json_with_duplicate_check",
    "load_available_filament_profiles",
]
