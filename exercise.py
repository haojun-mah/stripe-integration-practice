"""Candidate file. Complete the two TODO functions; helpers and CLI are provided."""

import argparse
import json
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:8765"
API_HEADERS = {
    "Authorization": "Bearer practice-map-key",
    "Accept": "image/png",
}


def write_png(image_bytes: bytes, output_path: str | Path) -> Path:
    """Provided: save successful image bytes and return the output path."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)
    return output


def render_map(
    payload: dict,
    output_path: str | Path,
    base_url: str = BASE_URL,
) -> Path:
    """Part 1: POST to /map.png, check success, and save the PNG.

    Use API_HEADERS and a finite timeout. Reuse write_png for the file write.
    Let Requests exceptions propagate on failure.
    """
    # TODO: implement the HTTP integration.
    raise NotImplementedError("Part 1: implement render_map")


def render_ride(
    ride_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
    base_url: str = BASE_URL,
) -> Path:
    """Part 2: read both JSON files, add ride overlays, and reuse render_map.

    Inputs are valid. The complete schema and grouping rules are in README.md.
    """
    # TODO: build the map request and call render_map.
    raise NotImplementedError("Part 2: implement render_ride")


def main(argv=None):
    """Provided: load a base config, or pass the two input files to render_ride."""
    parser = argparse.ArgumentParser(description="Render a base map or a bicycle ride.")
    parser.add_argument("mode", choices=("base", "ride"))
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args(argv)
    config_path = ROOT / "data" / "map_config.json"
    output = ROOT / "artifacts" / f"{args.mode}.png"
    try:
        if args.mode == "base":
            with config_path.open(encoding="utf-8") as file:
                payload = json.load(file)
            result = render_map(payload, output, base_url=args.base_url)
        else:
            result = render_ride(ROOT / "data" / "ride.json", config_path,
                                 output, base_url=args.base_url)
        print(f"Saved {result}")
        return 0
    except (NotImplementedError, requests.RequestException, OSError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
