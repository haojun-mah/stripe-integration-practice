"""Part 1: read a recorded GeoJSON ride."""

import json
import math
from pathlib import Path


class TrackFormatError(ValueError):
    """The input does not contain a usable ride."""


def load_positions(path: str | Path) -> list[dict[str, float]]:
    """Return map-coordinate objects in ride order; see CANDIDATE_BRIEF.md.

    The input file and its structure are part of the exercise: inspect data/ride.json.
    """
    # TODO: Part 1. Use json; translate file-format errors to TrackFormatError.
    raise NotImplementedError("Part 1: implement load_positions in bikemap/track.py")
