"""Tests for OrcaSlicer configuration module."""

from pathlib import Path
from typing import Optional

import pytest

from src.config import OrcaSlicerConfig
from src.config import Platform
from src.config import ProfileLocation
from src.config import ProfileType
from src.config import SearchPath
from src.config import build_search_path
from src.config import create_config
from src.config import detect_platform
from src.config import find_profile_path
from src.config import get_default_orcaslicer_dir
from src.config import list_profiles
from src.config import resolve_profile_path


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_detect_platform_returns_enum(self) -> None:
        """Test that detect_platform returns a Platform enum."""
        platform = detect_platform()
        assert isinstance(platform, Platform)

    def test_get_default_dir_macos(self) -> None:
        """Test default directory path for macOS."""
        path = get_default_orcaslicer_dir(Platform.MACOS)
        assert path.name == "OrcaSlicer"
        assert "Application Support" in str(path)
        assert path.is_absolute()

    def test_get_default_dir_windows(self) -> None:
        """Test default directory path for Windows."""
        path = get_default_orcaslicer_dir(Platform.WINDOWS)
        assert path.name == "OrcaSlicer"
        assert "AppData" in str(path) or "Roaming" in str(path)
        assert path.is_absolute()

    def test_get_default_dir_linux(self) -> None:
        """Test default directory path for Linux."""
        path = get_default_orcaslicer_dir(Platform.LINUX)
        assert path.name == "OrcaSlicer"
        assert ".config" in str(path)
        assert path.is_absolute()

    def test_get_default_dir_invalid_platform(self) -> None:
        """Test that invalid platform raises ValueError."""
        # Create a mock invalid platform by directly calling with wrong type
        with pytest.raises((ValueError, AttributeError)):
            get_default_orcaslicer_dir(None)  # type: ignore


class TestProfileLocationValidation:
    """Test ProfileLocation dataclass validation."""

    def test_profile_location_absolute_path_valid(self, tmp_path: Path) -> None:
        """Test ProfileLocation accepts absolute paths."""
        location = ProfileLocation(
            path=tmp_path,
            priority=10,
            source="test",
        )
        assert location.path == tmp_path

    def test_profile_location_relative_path_invalid(self) -> None:
        """Test ProfileLocation rejects relative paths."""
        with pytest.raises(ValueError, match="must be absolute"):
            ProfileLocation(
                path=Path("relative/path"),
                priority=10,
                source="test",
            )


class TestSearchPathValidation:
    """Test SearchPath dataclass validation."""

    def test_search_path_sorted_by_priority(self, tmp_path: Path) -> None:
        """Test SearchPath validates that locations are sorted by priority."""
        loc1 = ProfileLocation(path=tmp_path / "a", priority=10, source="first")
        loc2 = ProfileLocation(path=tmp_path / "b", priority=20, source="second")

        search_path = SearchPath(locations=(loc1, loc2), profile_type=ProfileType.FILAMENT)
        assert search_path.locations[0].priority == 10
        assert search_path.locations[1].priority == 20

    def test_search_path_unsorted_raises_error(self, tmp_path: Path) -> None:
        """Test SearchPath rejects unsorted locations."""
        loc1 = ProfileLocation(path=tmp_path / "a", priority=20, source="second")
        loc2 = ProfileLocation(path=tmp_path / "b", priority=10, source="first")

        with pytest.raises(ValueError, match="must be sorted"):
            SearchPath(locations=(loc1, loc2), profile_type=ProfileType.FILAMENT)


class TestConfigCreation:
    """Test OrcaSlicerConfig creation."""

    def test_config_with_absolute_base_dir(self, tmp_path: Path) -> None:
        """Test creating config with absolute base directory."""
        config = OrcaSlicerConfig(base_dir=tmp_path)
        assert config.base_dir == tmp_path
        assert config.user_profile == "default"
        assert config.samples_dir is None

    def test_config_with_relative_base_dir_raises_error(self) -> None:
        """Test creating config with relative base directory raises error."""
        with pytest.raises(ValueError, match="must be absolute"):
            OrcaSlicerConfig(base_dir=Path("relative"))

    def test_config_with_relative_samples_dir_raises_error(self, tmp_path: Path) -> None:
        """Test creating config with relative samples_dir raises error."""
        with pytest.raises(ValueError, match="must be absolute"):
            OrcaSlicerConfig(
                base_dir=tmp_path,
                samples_dir=Path("relative/samples"),
            )

    def test_config_with_custom_user_profile(self, tmp_path: Path) -> None:
        """Test creating config with custom user profile name."""
        config = OrcaSlicerConfig(
            base_dir=tmp_path,
            user_profile="custom_profile",
        )
        assert config.user_profile == "custom_profile"

    def test_config_with_all_parameters(self, tmp_path: Path) -> None:
        """Test creating config with all parameters specified."""
        samples = tmp_path / "samples"
        config = OrcaSlicerConfig(
            base_dir=tmp_path,
            user_profile="my_profile",
            samples_dir=samples,
        )
        assert config.base_dir == tmp_path
        assert config.user_profile == "my_profile"
        assert config.samples_dir == samples


class TestCreateConfigFactory:
    """Test create_config factory function."""

    def test_create_config_default_macos(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test create_config with auto-detected macOS path."""
        # Mock the platform detection
        monkeypatch.setattr("src.config.detect_platform", lambda: Platform.MACOS)

        # Create a fake home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        fake_orca_dir = fake_home / "Library" / "Application Support" / "OrcaSlicer"
        fake_orca_dir.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        config = create_config()
        assert config.user_profile == "default"
        assert config.samples_dir is None

    def test_create_config_with_override_dir(self, tmp_path: Path) -> None:
        """Test create_config with overridden config directory."""
        config = create_config(config_dir=tmp_path)
        assert config.base_dir == tmp_path

    def test_create_config_with_samples_dir(self, tmp_path: Path) -> None:
        """Test create_config with samples directory."""
        samples = tmp_path / "samples"
        config = create_config(config_dir=tmp_path, samples_dir=samples)
        assert config.samples_dir == samples

    def test_create_config_with_custom_user_profile(self, tmp_path: Path) -> None:
        """Test create_config with custom user profile."""
        config = create_config(
            config_dir=tmp_path,
            user_profile="production",
        )
        assert config.user_profile == "production"

    def test_create_config_missing_dir_no_samples_raises_error(self, tmp_path: Path) -> None:
        """Test create_config raises error when directory doesn't exist and no samples."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            create_config(config_dir=nonexistent)

    def test_create_config_missing_dir_with_samples_succeeds(self, tmp_path: Path) -> None:
        """Test create_config succeeds with missing dir if samples_dir provided."""
        nonexistent = tmp_path / "nonexistent"
        samples = tmp_path / "samples"
        config = create_config(config_dir=nonexistent, samples_dir=samples)
        assert config.base_dir == nonexistent


class TestBuildSearchPath:
    """Test build_search_path function."""

    def test_build_search_path_user_only(self, tmp_path: Path) -> None:
        """Test search path with only user directory."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path)
        search_path = build_search_path(config, ProfileType.FILAMENT)

        assert len(search_path.locations) == 1
        assert search_path.locations[0].path == user_dir
        assert search_path.locations[0].priority == 10
        assert search_path.locations[0].source == "user/default"

    def test_build_search_path_user_and_system(self, tmp_path: Path) -> None:
        """Test search path with user and system directories."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)

        system_vendor_dir = tmp_path / "system" / "Creality" / "filament"
        system_vendor_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path)
        search_path = build_search_path(config, ProfileType.FILAMENT)

        assert len(search_path.locations) == 2
        assert search_path.locations[0].priority == 10
        assert search_path.locations[1].priority == 20

    def test_build_search_path_multiple_vendors(self, tmp_path: Path) -> None:
        """Test search path with multiple vendor directories."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)

        creality_dir = tmp_path / "system" / "Creality" / "filament"
        creality_dir.mkdir(parents=True)

        qidi_dir = tmp_path / "system" / "Qidi" / "filament"
        qidi_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path)
        search_path = build_search_path(config, ProfileType.FILAMENT)

        # Should have user + both vendors
        assert len(search_path.locations) >= 3

    def test_build_search_path_with_samples(self, tmp_path: Path) -> None:
        """Test search path including samples directory."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)

        samples_vendor_dir = tmp_path / "samples" / "profiles" / "BBL" / "filament"
        samples_vendor_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=tmp_path / "samples")
        search_path = build_search_path(config, ProfileType.FILAMENT)

        # Should have user (10) and samples (30) at minimum
        priorities = [loc.priority for loc in search_path.locations]
        assert 10 in priorities
        assert 30 in priorities

    def test_build_search_path_sorted_by_priority(self, tmp_path: Path) -> None:
        """Test that search path locations are sorted by priority."""
        # Create all three levels
        user_dir = tmp_path / "user" / "default" / "machine"
        user_dir.mkdir(parents=True)

        system_dir = tmp_path / "system" / "BBL" / "machine"
        system_dir.mkdir(parents=True)

        samples_dir = tmp_path / "samples" / "profiles" / "Prusa" / "machine"
        samples_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=tmp_path / "samples")
        search_path = build_search_path(config, ProfileType.MACHINE)

        # Verify priorities are in order
        for i in range(len(search_path.locations) - 1):
            assert search_path.locations[i].priority <= search_path.locations[i + 1].priority

    def test_build_search_path_different_profile_types(self, tmp_path: Path) -> None:
        """Test search path with different profile types."""
        user_dir_filament = tmp_path / "user" / "default" / "filament"
        user_dir_filament.mkdir(parents=True)

        user_dir_machine = tmp_path / "user" / "default" / "machine"
        user_dir_machine.mkdir(parents=True)

        user_dir_process = tmp_path / "user" / "default" / "process"
        user_dir_process.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path)

        filament_path = build_search_path(config, ProfileType.FILAMENT)
        machine_path = build_search_path(config, ProfileType.MACHINE)
        process_path = build_search_path(config, ProfileType.PROCESS)

        assert filament_path.locations[0].path == user_dir_filament
        assert machine_path.locations[0].path == user_dir_machine
        assert process_path.locations[0].path == user_dir_process


class TestFindProfilePath:
    """Test find_profile_path function."""

    def test_find_profile_path_first_location(self, tmp_path: Path) -> None:
        """Test finding profile in first location."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        profile1 = dir1 / "test.json"
        profile1.write_text("{}")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        loc1 = ProfileLocation(path=dir1, priority=10, source="first")
        loc2 = ProfileLocation(path=dir2, priority=20, source="second")
        search_path = SearchPath(locations=(loc1, loc2), profile_type=ProfileType.FILAMENT)

        result = find_profile_path("test.json", search_path)
        assert result == profile1

    def test_find_profile_path_second_location(self, tmp_path: Path) -> None:
        """Test finding profile in second location when not in first."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        profile2 = dir2 / "test.json"
        profile2.write_text("{}")

        loc1 = ProfileLocation(path=dir1, priority=10, source="first")
        loc2 = ProfileLocation(path=dir2, priority=20, source="second")
        search_path = SearchPath(locations=(loc1, loc2), profile_type=ProfileType.FILAMENT)

        result = find_profile_path("test.json", search_path)
        assert result == profile2

    def test_find_profile_path_priority_order(self, tmp_path: Path) -> None:
        """Test that find returns first match by priority."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        profile1 = dir1 / "test.json"
        profile1.write_text("{}")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        profile2 = dir2 / "test.json"
        profile2.write_text("{}")

        loc1 = ProfileLocation(path=dir1, priority=10, source="first")
        loc2 = ProfileLocation(path=dir2, priority=20, source="second")
        search_path = SearchPath(locations=(loc1, loc2), profile_type=ProfileType.FILAMENT)

        result = find_profile_path("test.json", search_path)
        assert result == profile1

    def test_find_profile_path_not_found(self, tmp_path: Path) -> None:
        """Test finding non-existent profile returns None."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()

        loc1 = ProfileLocation(path=dir1, priority=10, source="first")
        search_path = SearchPath(locations=(loc1,), profile_type=ProfileType.FILAMENT)

        result = find_profile_path("nonexistent.json", search_path)
        assert result is None

    def test_find_profile_path_ignores_directories(self, tmp_path: Path) -> None:
        """Test that find_profile_path ignores directories."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        subdir = dir1 / "test.json"
        subdir.mkdir()

        loc1 = ProfileLocation(path=dir1, priority=10, source="first")
        search_path = SearchPath(locations=(loc1,), profile_type=ProfileType.FILAMENT)

        result = find_profile_path("test.json", search_path)
        assert result is None


class TestResolveProfilePath:
    """Test resolve_profile_path function."""

    def test_resolve_absolute_path_existing(self, tmp_path: Path) -> None:
        """Test resolving an absolute path that exists."""
        profile = tmp_path / "test.json"
        profile.write_text("{}")

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = resolve_profile_path(str(profile), config, ProfileType.FILAMENT)
        assert result == profile

    def test_resolve_absolute_path_nonexistent(self, tmp_path: Path) -> None:
        """Test resolving an absolute path that doesn't exist raises error."""
        profile = tmp_path / "nonexistent.json"
        config = OrcaSlicerConfig(base_dir=tmp_path)

        with pytest.raises(FileNotFoundError):
            resolve_profile_path(str(profile), config, ProfileType.FILAMENT)

    def test_resolve_absolute_path_is_directory(self, tmp_path: Path) -> None:
        """Test resolving an absolute path to a directory raises error."""
        config = OrcaSlicerConfig(base_dir=tmp_path)

        with pytest.raises(ValueError):
            resolve_profile_path(str(tmp_path), config, ProfileType.FILAMENT)

    def test_resolve_filename_in_user_directory(self, tmp_path: Path) -> None:
        """Test resolving filename from user directory."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)
        profile = user_dir / "test.json"
        profile.write_text("{}")

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = resolve_profile_path("test.json", config, ProfileType.FILAMENT)
        assert result == profile

    def test_resolve_filename_user_overrides_system(self, tmp_path: Path) -> None:
        """Test that user profile overrides system profile."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)
        user_profile = user_dir / "test.json"
        user_profile.write_text('{"name": "user"}')

        system_dir = tmp_path / "system" / "Creality" / "filament"
        system_dir.mkdir(parents=True)
        system_profile = system_dir / "test.json"
        system_profile.write_text('{"name": "system"}')

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = resolve_profile_path("test.json", config, ProfileType.FILAMENT)
        assert result == user_profile

    def test_resolve_filename_system_overrides_samples(self, tmp_path: Path) -> None:
        """Test that system profile overrides samples."""
        system_dir = tmp_path / "system" / "Creality" / "filament"
        system_dir.mkdir(parents=True)
        system_profile = system_dir / "test.json"
        system_profile.write_text('{"name": "system"}')

        samples_dir = tmp_path / "samples" / "profiles" / "BBL" / "filament"
        samples_dir.mkdir(parents=True)
        samples_profile = samples_dir / "test.json"
        samples_profile.write_text('{"name": "samples"}')

        config = OrcaSlicerConfig(base_dir=tmp_path, samples_dir=tmp_path / "samples")
        result = resolve_profile_path("test.json", config, ProfileType.FILAMENT)
        assert result == system_profile

    def test_resolve_filename_not_found_helpful_error(self, tmp_path: Path) -> None:
        """Test that missing file raises FileNotFoundError with helpful message."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            resolve_profile_path("missing.json", config, ProfileType.FILAMENT)

        error_msg = str(exc_info.value)
        assert "missing.json" in error_msg
        assert "not found" in error_msg

    def test_resolve_relative_path_raises_error(self, tmp_path: Path) -> None:
        """Test that relative paths (not just filenames) raise error."""
        config = OrcaSlicerConfig(base_dir=tmp_path)

        with pytest.raises(ValueError, match="Relative paths not supported"):
            resolve_profile_path("path/to/profile.json", config, ProfileType.FILAMENT)


class TestListProfiles:
    """Test list_profiles function."""

    def test_list_profiles_empty_directory(self, tmp_path: Path) -> None:
        """Test listing profiles from empty directory."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = list_profiles(config, ProfileType.FILAMENT)

        assert result == {}

    def test_list_profiles_from_user_directory(self, tmp_path: Path) -> None:
        """Test listing profiles from user directory."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)
        profile1 = user_dir / "profile1.json"
        profile1.write_text("{}")
        profile2 = user_dir / "profile2.json"
        profile2.write_text("{}")

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = list_profiles(config, ProfileType.FILAMENT)

        assert "user/default" in result
        assert len(result["user/default"]) == 2

    def test_list_profiles_multiple_sources(self, tmp_path: Path) -> None:
        """Test listing profiles from multiple sources."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)
        user_profile = user_dir / "user.json"
        user_profile.write_text("{}")

        system_dir = tmp_path / "system" / "Creality" / "filament"
        system_dir.mkdir(parents=True)
        system_profile = system_dir / "system.json"
        system_profile.write_text("{}")

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = list_profiles(config, ProfileType.FILAMENT)

        assert len(result) >= 2
        assert "user/default" in result
        assert "system/Creality" in result

    def test_list_profiles_sorted(self, tmp_path: Path) -> None:
        """Test that profiles are sorted by filename."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)
        profile_b = user_dir / "b.json"
        profile_b.write_text("{}")
        profile_a = user_dir / "a.json"
        profile_a.write_text("{}")
        profile_c = user_dir / "c.json"
        profile_c.write_text("{}")

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = list_profiles(config, ProfileType.FILAMENT)

        filenames = [p.name for p in result["user/default"]]
        assert filenames == sorted(filenames)

    def test_list_profiles_ignores_non_json(self, tmp_path: Path) -> None:
        """Test that only JSON files are listed."""
        user_dir = tmp_path / "user" / "default" / "filament"
        user_dir.mkdir(parents=True)
        profile_json = user_dir / "profile.json"
        profile_json.write_text("{}")
        profile_txt = user_dir / "readme.txt"
        profile_txt.write_text("text")

        config = OrcaSlicerConfig(base_dir=tmp_path)
        result = list_profiles(config, ProfileType.FILAMENT)

        assert len(result["user/default"]) == 1
        assert result["user/default"][0].name == "profile.json"

    def test_list_profiles_all_types(self, tmp_path: Path) -> None:
        """Test listing all profile types."""
        for profile_type in [ProfileType.FILAMENT, ProfileType.MACHINE, ProfileType.PROCESS]:
            profile_dir = tmp_path / "user" / "default" / profile_type.value
            profile_dir.mkdir(parents=True)
            profile = profile_dir / "test.json"
            profile.write_text("{}")

            config = OrcaSlicerConfig(base_dir=tmp_path)
            result = list_profiles(config, profile_type)

            assert "user/default" in result
            assert len(result["user/default"]) == 1
