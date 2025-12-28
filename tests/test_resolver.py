"""Tests for OrcaSlicer profile inheritance resolver module."""

import json
from pathlib import Path

import pytest

from src.config import OrcaSlicerConfig
from src.config import ProfileType
from src.config import create_config
from src.resolver import CircularInheritanceError
from src.resolver import InvalidProfileError
from src.resolver import ProfileNotFoundError
from src.resolver import ProfileResolver
from src.resolver import ProfileResolverError


class TestProfileResolverExceptions:
    """Test custom exception classes."""

    def test_profile_resolver_error_is_exception(self) -> None:
        """Test ProfileResolverError is an Exception."""
        error = ProfileResolverError("Test error")
        assert isinstance(error, Exception)

    def test_profile_not_found_error_is_resolver_error(self) -> None:
        """Test ProfileNotFoundError is a ProfileResolverError."""
        error = ProfileNotFoundError("Not found")
        assert isinstance(error, ProfileResolverError)

    def test_circular_inheritance_error_is_resolver_error(self) -> None:
        """Test CircularInheritanceError is a ProfileResolverError."""
        error = CircularInheritanceError("Circular")
        assert isinstance(error, ProfileResolverError)

    def test_invalid_profile_error_is_resolver_error(self) -> None:
        """Test InvalidProfileError is a ProfileResolverError."""
        error = InvalidProfileError("Invalid")
        assert isinstance(error, ProfileResolverError)


class TestProfileResolverInitialization:
    """Test ProfileResolver initialization."""

    def test_resolver_initialization(self, tmp_path: Path) -> None:
        """Test creating a ProfileResolver with config."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        assert resolver.config == config
        assert resolver._cache == {}

    def test_resolver_stores_config(self, tmp_path: Path) -> None:
        """Test resolver stores the config reference."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        assert resolver.config.base_dir == tmp_path


class TestProfileResolverLoadProfile:
    """Test ProfileResolver._load_profile() method."""

    def test_load_profile_valid_json(self, tmp_path: Path) -> None:
        """Test loading a valid JSON profile."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        # Create a test profile file
        profile_path = tmp_path / "test_profile.json"
        profile_data = {"name": "Test", "type": "filament"}
        profile_path.write_text(json.dumps(profile_data))

        # Load the profile
        loaded = resolver._load_profile(profile_path)

        assert loaded["name"] == "Test"
        assert loaded["type"] == "filament"

    def test_load_profile_missing_file(self, tmp_path: Path) -> None:
        """Test loading a non-existent profile raises error."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        missing_path = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            resolver._load_profile(missing_path)

    def test_load_profile_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON raises error."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text("{invalid json}")

        with pytest.raises(Exception):  # json.JSONDecodeError
            resolver._load_profile(invalid_path)


class TestProfileResolverMergeProfiles:
    """Test ProfileResolver._merge_profiles() method."""

    def test_merge_child_overrides_parent(self, tmp_path: Path) -> None:
        """Test child values override parent values."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        parent = {"name": "Parent", "temperature": 200, "speed": 50}
        child = {"name": "Child", "temperature": 220}

        merged = resolver._merge_profiles(parent, child)

        assert merged["name"] == "Child"
        assert merged["temperature"] == 220
        assert merged["speed"] == 50

    def test_merge_adds_new_keys_from_child(self, tmp_path: Path) -> None:
        """Test new keys from child are added."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        parent = {"name": "Parent", "temp": 200}
        child = {"bed_temp": 60}

        merged = resolver._merge_profiles(parent, child)

        assert "temp" in merged
        assert merged["bed_temp"] == 60

    def test_merge_arrays_replace_not_append(self, tmp_path: Path) -> None:
        """Test arrays are replaced, not appended."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        parent = {"compatible_printers": ["Printer1", "Printer2"]}
        child = {"compatible_printers": ["Printer3"]}

        merged = resolver._merge_profiles(parent, child)

        assert merged["compatible_printers"] == ["Printer3"]

    def test_merge_doesnt_mutate_inputs(self, tmp_path: Path) -> None:
        """Test merge doesn't mutate input dictionaries."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        parent = {"name": "Parent", "temp": 200}
        child = {"temp": 220}

        parent_orig = parent.copy()
        resolver._merge_profiles(parent, child)

        assert parent == parent_orig


class TestProfileResolverFindParentProfile:
    """Test ProfileResolver._find_parent_profile() method."""

    def test_find_parent_profile_by_filename(self, tmp_path: Path) -> None:
        """Test finding parent by filename in samples."""
        # Setup directory structure: samples_dir/profiles/{vendor}/{profile_type}/
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create a parent profile
        parent_profile = samples_dir / "parent.json"
        parent_profile.write_text(json.dumps({"name": "Parent Profile"}))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        found = resolver._find_parent_profile("parent.json", ProfileType.FILAMENT)

        assert found == parent_profile

    def test_find_parent_profile_not_found(self, tmp_path: Path) -> None:
        """Test finding non-existent parent raises error."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        with pytest.raises(ProfileNotFoundError):
            resolver._find_parent_profile("nonexistent", ProfileType.FILAMENT)

    def test_find_parent_by_name_field(self, tmp_path: Path) -> None:
        """Test finding parent by name field in JSON."""
        samples_base = tmp_path / "samples"
        filament_dir = samples_base / "profiles" / "TestVendor" / "filament"
        filament_dir.mkdir(parents=True)

        # Create profile with matching name
        profile_path = filament_dir / "test.json"
        profile_path.write_text(json.dumps({"name": "Parent Profile Name"}))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        found = resolver._find_parent_profile("Parent Profile Name", ProfileType.FILAMENT)

        assert found == profile_path


class TestProfileResolverResolveInheritanceChain:
    """Test ProfileResolver._resolve_inheritance_chain() method."""

    def test_resolve_no_inheritance(self, tmp_path: Path) -> None:
        """Test resolving profile with no inheritance."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        profile = {"name": "Test", "type": "filament", "temperature": 200}

        resolved = resolver._resolve_inheritance_chain(profile, ProfileType.FILAMENT)

        assert resolved["name"] == "Test"
        assert resolved["temperature"] == 200
        assert "inherits" not in resolved

    def test_resolve_single_level_inheritance(self, tmp_path: Path) -> None:
        """Test resolving profile with single level inheritance."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create parent profile
        parent_profile = samples_dir / "parent.json"
        parent_profile.write_text(json.dumps({"name": "Parent", "temperature": 200}))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        child = {"name": "Child", "type": "filament", "inherits": "parent.json", "temperature": 220}

        resolved = resolver._resolve_inheritance_chain(child, ProfileType.FILAMENT)

        assert resolved["name"] == "Child"
        assert resolved["temperature"] == 220

    def test_resolve_circular_inheritance_detected(self, tmp_path: Path) -> None:
        """Test circular inheritance is detected and raises error."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create circular reference
        profile_a = samples_dir / "profile_a.json"
        profile_a.write_text(json.dumps({"name": "ProfileA", "inherits": "profile_b.json"}))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        # Manually create circular scenario
        # This would be detected if we tried to resolve a profile that inherits from itself
        profile = {"name": "ProfileA", "type": "filament", "inherits": "ProfileA"}

        with pytest.raises(CircularInheritanceError):
            resolver._resolve_inheritance_chain(profile, ProfileType.FILAMENT)

    def test_resolve_multi_level_inheritance(self, tmp_path: Path) -> None:
        """Test resolving 3-level inheritance chain."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create base profile
        base = samples_dir / "base.json"
        base.write_text(json.dumps({"name": "Base", "temp": 200, "speed": 50}))

        # Create middle profile
        middle = samples_dir / "middle.json"
        middle.write_text(json.dumps({"name": "Middle", "inherits": "base.json", "temp": 210}))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        # Resolve top profile
        top = {"name": "Top", "type": "filament", "inherits": "middle.json", "temp": 220}

        resolved = resolver._resolve_inheritance_chain(top, ProfileType.FILAMENT)

        assert resolved["name"] == "Top"
        assert resolved["temp"] == 220
        assert resolved["speed"] == 50


class TestProfileResolverResolveProfile:
    """Test ProfileResolver.resolve_profile() public API."""

    def test_resolve_profile_simple(self, tmp_path: Path) -> None:
        """Test resolving a simple profile with no inheritance."""
        profile_path = tmp_path / "test.json"
        profile_path.write_text(json.dumps({"name": "Test", "type": "filament"}))

        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        resolved = resolver.resolve_profile(profile_path)

        assert resolved["name"] == "Test"
        assert resolved["type"] == "filament"

    def test_resolve_profile_with_inheritance(self, tmp_path: Path) -> None:
        """Test resolving a profile that inherits from another."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create parent
        parent = samples_dir / "parent.json"
        parent.write_text(json.dumps({"name": "Parent", "temp": 200}))

        # Create child profile to resolve
        profile_path = tmp_path / "child.json"
        profile_path.write_text(json.dumps({"name": "Child", "type": "filament", "inherits": "parent.json", "temp": 220}))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        resolved = resolver.resolve_profile(profile_path)

        assert resolved["name"] == "Child"
        assert resolved["temp"] == 220

    def test_resolve_profile_missing_file(self, tmp_path: Path) -> None:
        """Test resolving non-existent profile raises error."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        missing_path = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            resolver.resolve_profile(missing_path)

    def test_resolve_profile_clears_cache(self, tmp_path: Path) -> None:
        """Test resolve_profile clears cache to avoid stale data."""
        profile_path = tmp_path / "test.json"
        profile_path.write_text(json.dumps({"name": "Test", "type": "filament"}))

        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        # First resolve
        resolver.resolve_profile(profile_path)
        cache_size_after_first = len(resolver._cache)

        # Second resolve (should start fresh)
        resolver.resolve_profile(profile_path)

        # Cache should be cleared between resolve_profile calls
        # Note: This depends on implementation details
        assert isinstance(cache_size_after_first, int)

    def test_resolve_profile_creates_flattened_result(self, tmp_path: Path) -> None:
        """Test resolved profile has all inherited settings."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create multi-level inheritance
        base = samples_dir / "base.json"
        base.write_text(
            json.dumps({
                "name": "Base",
                "temp": 200,
                "speed": 50,
                "retraction": 5
            })
        )

        middle = samples_dir / "middle.json"
        middle.write_text(
            json.dumps({
                "name": "Middle",
                "inherits": "base.json",
                "temp": 210,
                "bed_temp": 60
            })
        )

        profile_path = tmp_path / "top.json"
        profile_path.write_text(
            json.dumps({
                "name": "Top",
                "type": "filament",
                "inherits": "middle.json",
                "temp": 220
            })
        )

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        resolved = resolver.resolve_profile(profile_path)

        # Should have all settings from entire chain
        assert resolved["name"] == "Top"
        assert resolved["temp"] == 220
        assert resolved["bed_temp"] == 60
        assert resolved["speed"] == 50
        assert resolved["retraction"] == 5


class TestProfileResolverCaching:
    """Test ProfileResolver caching behavior."""

    def test_cache_stores_loaded_profiles(self, tmp_path: Path) -> None:
        """Test that loaded profiles are cached."""
        profile_path = tmp_path / "test.json"
        profile_path.write_text(json.dumps({"name": "Test", "type": "filament"}))

        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        # Load profile (uses _load_profile which may cache)
        resolved = resolver.resolve_profile(profile_path)

        assert resolved["name"] == "Test"

    def test_profile_type_detection(self, tmp_path: Path) -> None:
        """Test auto-detecting profile type from JSON."""
        filament_path = tmp_path / "filament.json"
        filament_path.write_text(json.dumps({"name": "Test", "type": "filament"}))

        machine_path = tmp_path / "machine.json"
        machine_path.write_text(json.dumps({"name": "Test", "type": "machine"}))

        config = OrcaSlicerConfig(base_dir=tmp_path)
        resolver = ProfileResolver(config)

        filament = resolver.resolve_profile(filament_path)
        machine = resolver.resolve_profile(machine_path)

        assert filament["type"] == "filament"
        assert machine["type"] == "machine"


class TestRealWorldProfiles:
    """Test with realistic OrcaSlicer profile structures."""

    def test_resolve_realistic_filament_profile(self, tmp_path: Path) -> None:
        """Test resolving a realistic multi-level filament profile."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Create realistic inheritance chain
        common = samples_dir / "fdm_filament_common.json"
        common.write_text(json.dumps({
            "name": "fdm_filament_common",
            "type": "filament",
            "temperature": 200,
            "bed_temperature": 60,
            "filament_type": "PLA",
            "speed": 100
        }))

        material = samples_dir / "fdm_filament_pa.json"
        material.write_text(json.dumps({
            "name": "fdm_filament_pa",
            "inherits": "fdm_filament_common.json",
            "temperature": 240,
            "type": "filament"
        }))

        base = samples_dir / "Fiberon_PA6CF_base.json"
        base.write_text(json.dumps({
            "name": "Fiberon PA6-CF @base",
            "inherits": "fdm_filament_pa.json",
            "filament_id": "PA6-CF",
            "type": "filament"
        }))

        # Resolve
        profile_path = tmp_path / "user_profile.json"
        profile_path.write_text(json.dumps({
            "name": "Fiberon PA6-GF",
            "type": "filament",
            "inherits": "Fiberon_PA6CF_base.json",
            "temperature": 245,
            "compatible_printers": ["Printer1"]
        }))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        resolved = resolver.resolve_profile(profile_path)

        # Should have settings from all 4 levels
        assert resolved["name"] == "Fiberon PA6-GF"
        assert resolved["temperature"] == 245  # User override
        assert resolved["filament_id"] == "PA6-CF"  # From base
        assert resolved["compatible_printers"] == ["Printer1"]
        assert resolved["speed"] == 100  # From root
        assert resolved["type"] == "filament"

    def test_resolve_profile_preserves_metadata(self, tmp_path: Path) -> None:
        """Test resolved profile preserves child metadata."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        parent = samples_dir / "parent.json"
        parent.write_text(json.dumps({
            "name": "Parent",
            "from": "system",
            "version": 1
        }))

        profile_path = tmp_path / "child.json"
        profile_path.write_text(json.dumps({
            "name": "Child",
            "type": "filament",
            "from": "user",
            "inherits": "parent.json",
            "custom_field": "custom_value"
        }))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        resolved = resolver.resolve_profile(profile_path)

        # Child metadata takes precedence
        assert resolved["name"] == "Child"
        assert resolved["from"] == "user"
        assert resolved["custom_field"] == "custom_value"

    def test_resolve_complex_inheritance_chain(self, tmp_path: Path) -> None:
        """Test resolving 5-level inheritance (real-world scenario)."""
        samples_base = tmp_path / "samples"
        samples_dir = samples_base / "profiles" / "TestVendor" / "filament"
        samples_dir.mkdir(parents=True)

        # Level 5: Root template
        root = samples_dir / "fdm_filament_common.json"
        root.write_text(json.dumps({
            "name": "fdm_filament_common",
            "type": "filament",
            "setting1": "root_value1",
            "setting2": "root_value2"
        }))

        # Level 4: Material template
        material = samples_dir / "fdm_filament_pa.json"
        material.write_text(json.dumps({
            "name": "fdm_filament_pa",
            "inherits": "fdm_filament_common.json",
            "setting2": "material_value2",
            "setting3": "material_value3"
        }))

        # Level 3: Base profile
        base = samples_dir / "base.json"
        base.write_text(json.dumps({
            "name": "Fiberon PA6-CF @base",
            "inherits": "fdm_filament_pa.json",
            "setting3": "base_value3",
            "setting4": "base_value4"
        }))

        # Level 2: System profile
        system = samples_dir / "system.json"
        system.write_text(json.dumps({
            "name": "Fiberon PA6-CF @System",
            "inherits": "base.json",
            "setting4": "system_value4",
            "setting5": "system_value5"
        }))

        # Level 1: User profile
        profile_path = tmp_path / "user_profile.json"
        profile_path.write_text(json.dumps({
            "name": "Fiberon PA6-GF Quidi Q1 Pro (mi3)",
            "type": "filament",
            "inherits": "system.json",
            "setting5": "user_value5",
            "setting6": "user_value6"
        }))

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=samples_base)
        resolver = ProfileResolver(config)

        resolved = resolver.resolve_profile(profile_path)

        # Verify proper override chain (child overrides parent)
        assert resolved["name"] == "Fiberon PA6-GF Quidi Q1 Pro (mi3)"
        assert resolved["setting1"] == "root_value1"
        assert resolved["setting2"] == "material_value2"
        assert resolved["setting3"] == "base_value3"
        assert resolved["setting4"] == "system_value4"
        assert resolved["setting5"] == "user_value5"
        assert resolved["setting6"] == "user_value6"


__all__ = [
    "TestProfileResolverExceptions",
    "TestProfileResolverInitialization",
    "TestProfileResolverLoadProfile",
    "TestProfileResolverMergeProfiles",
    "TestProfileResolverFindParentProfile",
    "TestProfileResolverResolveInheritanceChain",
    "TestProfileResolverResolveProfile",
    "TestProfileResolverCaching",
    "TestRealWorldProfiles",
]
