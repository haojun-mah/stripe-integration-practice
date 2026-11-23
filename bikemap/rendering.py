"""The CLI uses these functions to save images and construct overlays."""

from copy import deepcopy
from pathlib import Path


def base_map_payload(config: dict) -> dict:
    """Provided: callers get their own payload so config is not modified."""
    return deepcopy(config)


def save_image(image: bytes, output: str | Path) -> Path:
    """Write successful response bytes, creating parent directories as needed."""
    # TODO: Part 1. Return a pathlib.Path for the written image.
    raise NotImplementedError("Part 1: implement save_image in bikemap/rendering.py")


def build_route_payload(
    positions: list[dict[str, float]],
    config: dict,
    segments_per_path: int = 10,
) -> dict:
    """Add ride overlays to the configured map; do not mutate either input."""
    # TODO: Part 2. See the brief for marker, path, and boundary requirements.
    raise NotImplementedError("Part 2: implement build_route_payload in bikemap/rendering.py")
