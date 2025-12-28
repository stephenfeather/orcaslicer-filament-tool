"""Profile inheritance resolver for OrcaSlicer configurations."""

import copy
from pathlib import Path
from typing import Any

from src.config import OrcaSlicerConfig
from src.config import ProfileType
from src.config import build_search_path
from src.parser import load_profile


# Custom exceptions
class ProfileResolverError(Exception):
    """Base exception for profile resolver errors."""


class ProfileNotFoundError(ProfileResolverError):
    """Raised when a profile cannot be found."""


class CircularInheritanceError(ProfileResolverError):
    """Raised when circular inheritance is detected."""


class InvalidProfileError(ProfileResolverError):
    """Raised when a profile is invalid."""


class ProfileResolver:
    """Resolves inheritance chains for OrcaSlicer profiles."""

    def __init__(self, config: OrcaSlicerConfig) -> None:
        """
        Initialize ProfileResolver.

        Args:
            config: OrcaSlicerConfig with base directory and search paths

        Examples:
            >>> from src.config import create_config
            >>> config = create_config()
            >>> resolver = ProfileResolver(config)
        """
        self.config = config
        self._cache: dict[str, dict[str, Any]] = {}

    def resolve_profile(self, profile_path: Path) -> dict[str, Any]:
        """
        Resolve a profile's full inheritance chain.

        Loads a profile and recursively resolves all inherited settings,
        returning a flattened configuration with all values merged from
        the entire inheritance chain.

        Args:
            profile_path: Absolute path to profile file to resolve

        Returns:
            Fully resolved profile dictionary with all inherited settings merged

        Raises:
            FileNotFoundError: If profile file doesn't exist
            json.JSONDecodeError: If profile JSON is invalid
            CircularInheritanceError: If circular inheritance detected
            ProfileNotFoundError: If referenced parent profile not found

        Examples:
            >>> from pathlib import Path
            >>> from src.config import create_config
            >>> config = create_config()
            >>> resolver = ProfileResolver(config)
            >>> resolved = resolver.resolve_profile(Path("/path/to/profile.json"))
            >>> print(resolved["name"])
        """
        # Clear cache at start of resolve to avoid stale data
        self._cache.clear()

        # Load the profile
        profile = self._load_profile(profile_path)

        # Detect profile type from the profile JSON, or infer from directory
        profile_type = self._get_profile_type(profile, profile_path)

        # Resolve inheritance chain
        resolved = self._resolve_inheritance_chain(profile, profile_type)

        return resolved

    def _load_profile(self, profile_path: Path) -> dict[str, Any]:
        """
        Load and parse a profile JSON file.

        Args:
            profile_path: Path to profile JSON file

        Returns:
            Parsed profile dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        return load_profile(profile_path)

    def _get_profile_type(
        self, profile: dict[str, Any], profile_path: Path | None = None
    ) -> ProfileType:
        """
        Detect profile type from profile JSON or directory structure.

        If the profile JSON has a "type" field, use that. Otherwise,
        infer from the directory structure (filament, machine, process).

        Args:
            profile: Profile dictionary from JSON
            profile_path: Optional path to profile file for directory inference

        Returns:
            ProfileType enum value

        Raises:
            InvalidProfileError: If type cannot be determined
        """
        # First, try to get type from profile JSON
        type_str = profile.get("type", "").lower()

        if type_str == "filament":
            return ProfileType.FILAMENT
        if type_str == "machine":
            return ProfileType.MACHINE
        if type_str == "process":
            return ProfileType.PROCESS

        # If no type in JSON, try to infer from directory structure
        if profile_path and profile_path.parent.name in (
            "filament",
            "machine",
            "process",
        ):
            dir_type = profile_path.parent.name.lower()
            if dir_type == "filament":
                return ProfileType.FILAMENT
            if dir_type == "machine":
                return ProfileType.MACHINE
            if dir_type == "process":
                return ProfileType.PROCESS

        raise InvalidProfileError(
            f"Unknown profile type: {type_str}. "
            "Set 'type' field in profile or place in "
            "filament/machine/process directory."
        )

    def _find_parent_profile(
        self, parent_name: str, profile_type: ProfileType
    ) -> Path:
        """
        Find parent profile by name.

        Searches for a profile in priority order: user, system, samples.
        First tries exact filename match, then searches for a profile
        with matching "name" field in JSON.

        Args:
            parent_name: Name of parent profile to find
                (with or without .json extension)
            profile_type: Type of profile (filament, machine, process)

        Returns:
            Absolute path to parent profile

        Raises:
            ProfileNotFoundError: If parent cannot be found
        """
        search_path = build_search_path(self.config, profile_type)

        # Normalize parent_name: add .json if not already present
        if not parent_name.endswith(".json"):
            filename = f"{parent_name}.json"
        else:
            filename = parent_name

        # Search each location in priority order
        for location in search_path.locations:
            if not location.path.exists():
                continue

            # Try exact filename match first
            candidate = location.path / filename
            if candidate.exists():
                return candidate

            # Try recursive search for profile by name field
            if location.path.is_dir():
                for json_file in location.path.rglob("*.json"):
                    try:
                        data = load_profile(json_file)
                        # Match by "name" field or parent_name without extension
                        profile_name = data.get("name")
                        parent_without_ext = parent_name.replace(".json", "")
                        if profile_name in (parent_name, parent_without_ext):
                            return json_file
                    except (FileNotFoundError, ValueError):
                        # Skip files that can't be loaded
                        continue

        raise ProfileNotFoundError(
            f"Parent profile not found: {parent_name}"
        )

    def _merge_profiles(
        self, parent: dict[str, Any], child: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge child profile into parent profile.

        Child settings override parent settings. Arrays are replaced,
        not appended. Creates a deep copy to avoid mutating inputs.

        Args:
            parent: Parent profile (base)
            child: Child profile (overrides)

        Returns:
            Merged profile dictionary with child overriding parent

        Examples:
            >>> parent = {"temp": 200, "speed": 50}
            >>> child = {"temp": 220}
            >>> merged = resolver._merge_profiles(parent, child)
            >>> merged["temp"]
            220
            >>> merged["speed"]
            50
        """
        # Create deep copy of parent to avoid mutation
        merged = copy.deepcopy(parent)

        # Override with child values
        for key, value in child.items():
            merged[key] = copy.deepcopy(value)

        return merged

    def _resolve_inheritance_chain(
        self,
        profile: dict[str, Any],
        profile_type: ProfileType,
        visited: set[str] | None = None,
    ) -> dict[str, Any]:
        """
        Recursively resolve inheritance chain and merge settings.

        Traverses up the inheritance tree to the root, then merges
        down (root -> leaf) so child settings override parent settings.
        Detects circular inheritance.

        Args:
            profile: Profile to resolve
            profile_type: Type of profile
            visited: Set of visited profile names (for circular detection)

        Returns:
            Fully resolved profile with all inherited settings merged

        Raises:
            CircularInheritanceError: If circular inheritance detected
            ProfileNotFoundError: If parent profile not found
        """
        if visited is None:
            visited = set()

        profile_name = profile.get("name", "unknown")

        # Detect circular inheritance
        if profile_name in visited:
            chain = " -> ".join(list(visited) + [profile_name])
            raise CircularInheritanceError(f"Circular inheritance detected: {chain}")

        visited.add(profile_name)

        # Base case: no inheritance
        if "inherits" not in profile:
            return copy.deepcopy(profile)

        # Recursive case: resolve parent first
        parent_name = profile["inherits"]
        parent_path = self._find_parent_profile(parent_name, profile_type)
        parent_profile = self._load_profile(parent_path)

        # Recursively resolve parent's inheritance chain
        resolved_parent = self._resolve_inheritance_chain(
            parent_profile, profile_type, visited.copy()
        )

        # Merge current profile into resolved parent (child overrides parent)
        return self._merge_profiles(resolved_parent, profile)


__all__ = [
    "ProfileResolverError",
    "ProfileNotFoundError",
    "CircularInheritanceError",
    "InvalidProfileError",
    "ProfileResolver",
]
