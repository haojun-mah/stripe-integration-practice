import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

from bikemap.client import MapClient
from bikemap.rendering import build_route_payload, save_image
from bikemap.track import load_positions

ROOT = Path(__file__).resolve().parents[1]
subject = SimpleNamespace(
    MapClient=MapClient,
    build_route_payload=build_route_payload,
    save_image=save_image,
    load_positions=load_positions,
)


def config():
    return json.loads((ROOT / "data" / "map_config.json").read_text(encoding="utf-8"))


def track_document(coordinates):
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {},
                      "geometry": {"type": "LineString", "coordinates": coordinates}}],
    }


def load_document(document):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ride.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return subject.load_positions(path)
