"""REFERENCE ANSWER -- SPOILERS. Candidate files remain unfinished."""

from copy import deepcopy
import json
from pathlib import Path

import requests

from bikemap.client import MapAPIError, MapClient as StarterMapClient
from bikemap.track import TrackFormatError


def load_positions(path):
    with Path(path).open(encoding="utf-8") as handle:
        try:
            document = json.load(handle)
        except json.JSONDecodeError as exc:
            raise TrackFormatError("Invalid JSON") from exc
    try:
        if document["type"] != "FeatureCollection":
            raise TrackFormatError("Expected a FeatureCollection")
        geometry = document["features"][0]["geometry"]
        if geometry["type"] != "LineString":
            raise TrackFormatError("Expected a LineString")
        coordinates = geometry["coordinates"]
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise TrackFormatError("A ride needs at least two coordinates")
        positions = []
        for coordinate in coordinates:
            if not isinstance(coordinate, list) or len(coordinate) not in (2, 3):
                raise TrackFormatError("Expected a two- or three-component coordinate")
            lon, lat = coordinate[:2]
            if type(lon) not in (int, float) or type(lat) not in (int, float):
                raise TrackFormatError("Coordinates must be numbers")
            # These comparisons also reject infinity and NaN.
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise TrackFormatError("Coordinate is not finite or is out of range")
            positions.append({"lat": lat, "lon": lon})
        return positions
    except (KeyError, IndexError, TypeError) as exc:
        raise TrackFormatError("Missing or invalid GeoJSON track structure") from exc


class MapClient(StarterMapClient):
    def render(self, payload):
        try:
            response = self.session.post(
                self.base_url + "/map.png",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "image/png"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            if response is not None:
                raise MapAPIError(
                    f"Map HTTP {response.status_code}: {response.text[:500]}", response.status_code
                ) from exc
            raise MapAPIError(f"Map transport error: {exc}") from exc
        media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type != "image/png":
            raise MapAPIError(f"Expected image/png, got {media_type!r}", response.status_code)
        return response.content


def save_image(image, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    return output


def build_route_payload(positions, config, segments_per_path=10):
    if len(positions) < 2:
        raise ValueError("A ride needs at least two positions")
    if type(segments_per_path) is not int or segments_per_path <= 0:
        raise ValueError("segments_per_path must be a positive integer")
    payload = deepcopy(config)
    positions = deepcopy(positions)
    payload["markers"] = [
        {"color": "white", "label": "Start", "coord": positions[0]},
        {"color": "blue", "label": "Stripe", "coord": positions[-1]},
    ]
    payload["paths"] = [
        {"color": "blue" if group % 2 == 0 else "brown",
         "positions": positions[start:start + segments_per_path + 1]}
        for group, start in enumerate(range(0, len(positions) - 1, segments_per_path))
    ]
    return payload
