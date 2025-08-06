# Functions used in this project

from pathlib import Path
import glob


def get_single_match(base_path, pattern):
    """Get exactly one file matching the pattern in base_path.

    Args:
        base_path: Path object - base directory to search in
        pattern: str - glob pattern (can include subdirectories)

    Returns:
        Path: Single matching file path
    """
    if not isinstance(base_path, Path):
        raise TypeError(f"base_path must be a Path object, got {type(base_path)}")

    # Use glob.glob for complex patterns with subdirectories
    full_pattern = str(base_path / pattern)
    matches = glob.glob(full_pattern)

    # Convert back to Path objects
    matches = [Path(m) for m in matches]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        raise ValueError(f"No matches found for pattern '{pattern}' in {base_path}")
    else:
        raise ValueError(f"Multiple matches found for pattern '{pattern}': {matches}")
