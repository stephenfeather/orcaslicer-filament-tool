"""OrcaSlicer configuration module for path detection and profile loading."""

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Platform(Enum):
    """Supported operating system platforms."""

    MACOS = "darwin"
    WINDOWS = "win32"
    LINUX = "linux"


class ProfileType(Enum):
    """Types of OrcaSlicer profiles."""

    FILAMENT = "filament"
    MACHINE = "machine"
    PROCESS = "process"


@dataclass(frozen=True)
class ProfileLocation:
    """
    Represents a single location where profiles can be found.

    Attributes:
        path: Absolute path to the profile directory
        priority: Search priority (lower = higher priority)
        source: Description of the source (e.g., "user", "system", "samples")
    """

    path: Path
    priority: int
    source: str

    def __post_init__(self) -> None:
        """Validate that path is absolute."""
        if not self.path.is_absolute():
            raise ValueError(f"ProfileLocation path must be absolute: {self.path}")


@dataclass(frozen=True)
class SearchPath:
    """
    Collection of profile locations to search, ordered by priority.

    Attributes:
        locations: Tuple of ProfileLocation objects, ordered by priority
        profile_type: Type of profile to search for
    """

    locations: tuple[ProfileLocation, ...]
    profile_type: ProfileType

    def __post_init__(self) -> None:
        """Validate that locations are sorted by priority."""
        priorities = [loc.priority for loc in self.locations]
        if priorities != sorted(priorities):
            raise ValueError("SearchPath locations must be sorted by priority")


@dataclass(frozen=True)
class OrcaSlicerConfig:
    """
    Configuration for OrcaSlicer directory structure and profile search paths.

    Attributes:
        base_dir: Base OrcaSlicer configuration directory
        user_profile: User profile name (default: "default")
        samples_dir: Optional path to samples directory for fallback
    """

    base_dir: Path
    user_profile: str = "default"
    samples_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        """Validate paths are absolute."""
        if not self.base_dir.is_absolute():
            raise ValueError(f"base_dir must be absolute: {self.base_dir}")
        if self.samples_dir is not None and not self.samples_dir.is_absolute():
            raise ValueError(f"samples_dir must be absolute: {self.samples_dir}")


def detect_platform() -> Platform:
    """
    Detect the current operating system platform.

    Returns:
        Platform enum value

    Raises:
        RuntimeError: If platform is not supported

    Examples:
        >>> detect_platform()  # On macOS
        <Platform.MACOS: 'darwin'>
    """
    platform_map = {
        "darwin": Platform.MACOS,
        "win32": Platform.WINDOWS,
        "linux": Platform.LINUX,
    }

    platform = platform_map.get(sys.platform)
    if platform is None:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    return platform


def get_default_orcaslicer_dir(platform: Platform) -> Path:
    """
    Get the default OrcaSlicer configuration directory for a platform.

    Args:
        platform: The target platform

    Returns:
        Path to default OrcaSlicer directory (may not exist)

    Examples:
        >>> get_default_orcaslicer_dir(Platform.MACOS)
        PosixPath('/Users/username/Library/Application Support/OrcaSlicer')
    """
    if platform == Platform.MACOS:
        return Path.home() / "Library" / "Application Support" / "OrcaSlicer"
    if platform == Platform.WINDOWS:
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "OrcaSlicer"
    if platform == Platform.LINUX:
        return Path.home() / ".config" / "OrcaSlicer"

    raise ValueError(f"Unknown platform: {platform}")


def build_search_path(
    config: OrcaSlicerConfig,
    profile_type: ProfileType,
) -> SearchPath:
    """
    Build a prioritized search path for a specific profile type.

    Priority order:
    1. user/ directory (priority 10)
    2. system/ directory (priority 20)
    3. samples/ directory if configured (priority 30)

    Args:
        config: OrcaSlicer configuration
        profile_type: Type of profile to search for

    Returns:
        SearchPath with ordered locations

    Examples:
        >>> config = OrcaSlicerConfig(base_dir=Path("/home/user/.config/OrcaSlicer"))
        >>> search_path = build_search_path(config, ProfileType.FILAMENT)
        >>> len(search_path.locations)
        0
    """
    locations: list[ProfileLocation] = []

    # Priority 1: User profiles
    user_dir = config.base_dir / "user" / config.user_profile / profile_type.value
    if user_dir.exists():
        locations.append(
            ProfileLocation(
                path=user_dir,
                priority=10,
                source=f"user/{config.user_profile}",
            )
        )

    # Priority 2: System profiles (vendor-installed)
    system_base = config.base_dir / "system"
    if system_base.exists():
        for vendor_dir in system_base.iterdir():
            if vendor_dir.is_dir():
                profile_dir = vendor_dir / profile_type.value
                if profile_dir.exists():
                    locations.append(
                        ProfileLocation(
                            path=profile_dir,
                            priority=20,
                            source=f"system/{vendor_dir.name}",
                        )
                    )

    # Priority 3: Samples fallback
    if config.samples_dir is not None:
        samples_profiles = config.samples_dir / "profiles"
        if samples_profiles.exists():
            for vendor_dir in samples_profiles.iterdir():
                if vendor_dir.is_dir() and not vendor_dir.name.endswith(".json"):
                    profile_dir = vendor_dir / profile_type.value
                    if profile_dir.exists():
                        locations.append(
                            ProfileLocation(
                                path=profile_dir,
                                priority=30,
                                source=f"samples/{vendor_dir.name}",
                            )
                        )

    # Sort by priority (should already be sorted due to insertion order)
    sorted_locations = tuple(sorted(locations, key=lambda loc: loc.priority))

    return SearchPath(locations=sorted_locations, profile_type=profile_type)


def find_profile_path(
    filename: str,
    search_path: SearchPath,
) -> Optional[Path]:
    """
    Find a profile file by searching locations in priority order.

    Args:
        filename: Name of the profile file (e.g., "Generic PLA.json")
        search_path: SearchPath to search through

    Returns:
        Absolute path to the profile file, or None if not found

    Examples:
        >>> search_path = SearchPath(locations=(), profile_type=ProfileType.FILAMENT)
        >>> find_profile_path("test.json", search_path)
    """
    for location in search_path.locations:
        candidate = location.path / filename
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def resolve_profile_path(
    input_path: str,
    config: OrcaSlicerConfig,
    profile_type: ProfileType,
) -> Path:
    """
    Resolve a profile path from either a filename or full path.

    This is the main entry point for path resolution, supporting both:
    1. Filename only: "Generic PLA.json" -> searches in priority order
    2. Absolute path: "/full/path/to/profile.json" -> validates and returns

    Args:
        input_path: Either a filename or absolute path
        config: OrcaSlicer configuration
        profile_type: Type of profile being resolved

    Returns:
        Absolute path to the profile file

    Raises:
        FileNotFoundError: If profile cannot be found
        ValueError: If input_path is a relative path (not filename)

    Examples:
        >>> # Filename search
        >>> config = OrcaSlicerConfig(base_dir=Path("/tmp"))
        >>> path = resolve_profile_path("test.json", config, ProfileType.FILAMENT)
        Traceback (most recent call last):
        ...
        FileNotFoundError: Profile 'test.json' not found in search paths:
    """
    path_obj = Path(input_path)

    # Case 1: Absolute path provided
    if path_obj.is_absolute():
        if not path_obj.exists():
            raise FileNotFoundError(f"Profile not found: {path_obj}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path_obj}")
        return path_obj

    # Case 2: Relative path (not just filename) - reject for clarity
    if len(path_obj.parts) > 1:
        msg = (
            "Relative paths not supported. Use filename only or absolute path: "
            f"{input_path}"
        )
        raise ValueError(msg)

    # Case 3: Filename only - search in priority order
    search_path = build_search_path(config, profile_type)
    found_path = find_profile_path(input_path, search_path)

    if found_path is None:
        # Build helpful error message
        searched_dirs = [str(loc.path) for loc in search_path.locations]
        error_msg = f"Profile '{input_path}' not found in search paths:"
        if searched_dirs:
            error_msg += "\n" + "\n".join(f"  - {d}" for d in searched_dirs)
        raise FileNotFoundError(error_msg)

    return found_path


def create_config(
    config_dir: Optional[Path] = None,
    user_profile: str = "default",
    samples_dir: Optional[Path] = None,
    platform: Optional[Platform] = None,
) -> OrcaSlicerConfig:
    """
    Create an OrcaSlicer configuration.

    This is the main factory function for creating configurations.

    Args:
        config_dir: Override for OrcaSlicer base directory (None = auto-detect)
        user_profile: User profile name (default: "default")
        samples_dir: Optional path to samples directory for fallback
        platform: Override platform detection (for testing)

    Returns:
        OrcaSlicerConfig instance

    Raises:
        FileNotFoundError: If auto-detected config directory doesn't exist

    Examples:
        >>> # Auto-detect with defaults
        >>> config = create_config()

        >>> # Override config directory
        >>> config = create_config(config_dir=Path("/custom/orcaslicer"))
    """
    # Detect platform if not provided
    if platform is None:
        platform = detect_platform()

    # Determine base directory
    if config_dir is None:
        base_dir = get_default_orcaslicer_dir(platform)
        # Don't require it to exist - might only use samples
    else:
        base_dir = config_dir

    # Validate base_dir if it's meant to be used
    if samples_dir is None and not base_dir.exists():
        raise FileNotFoundError(
            f"OrcaSlicer directory not found: {base_dir}\n"
            f"Use --config-dir to specify location or provide samples_dir fallback"
        )

    return OrcaSlicerConfig(
        base_dir=base_dir,
        user_profile=user_profile,
        samples_dir=samples_dir,
    )


def list_profiles(
    config: OrcaSlicerConfig,
    profile_type: ProfileType,
) -> dict[str, list[Path]]:
    """
    List all available profiles of a given type, grouped by source.

    Args:
        config: OrcaSlicer configuration
        profile_type: Type of profiles to list

    Returns:
        Dictionary mapping source names to lists of profile paths

    Examples:
        >>> config = OrcaSlicerConfig(base_dir=Path("/tmp"))
        >>> profiles = list_profiles(config, ProfileType.FILAMENT)
        >>> profiles
        {}
    """
    search_path = build_search_path(config, profile_type)
    results: dict[str, list[Path]] = {}

    for location in search_path.locations:
        profile_files = [f for f in location.path.glob("*.json") if f.is_file()]
        if profile_files:
            results[location.source] = sorted(profile_files)

    return results


__all__ = [
    "Platform",
    "ProfileType",
    "ProfileLocation",
    "SearchPath",
    "OrcaSlicerConfig",
    "detect_platform",
    "get_default_orcaslicer_dir",
    "create_config",
    "build_search_path",
    "find_profile_path",
    "resolve_profile_path",
    "list_profiles",
]
