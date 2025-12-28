"""Parser for OrcaSlicer JSON profile files."""

import json
from pathlib import Path
from typing import Any


def load_profile(profile_path: Path) -> dict[str, Any]:
    """
    Load a profile JSON file.

    Args:
        profile_path: Absolute path to profile file

    Returns:
        Parsed JSON as dictionary

    Raises:
        FileNotFoundError: If profile file doesn't exist
        json.JSONDecodeError: If file is not valid JSON

    Examples:
        >>> profile = load_profile(Path("/path/to/profile.json"))
        >>> profile["type"]
        'filament'
    """
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    if not profile_path.is_file():
        raise ValueError(f"Path is not a file: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["load_profile"]
