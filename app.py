"""Provided CLI. Candidate work lives in the three bikemap modules."""

import argparse
import json
from pathlib import Path
import sys

import requests

from bikemap.client import MapAPIError, MapClient
from bikemap.rendering import base_map_payload, build_route_payload, save_image
from bikemap.track import load_positions

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render a recorded bicycle ride.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "inspect", "base", "route"):
        command = commands.add_parser(name)
        command.add_argument("--input", type=Path, default=ROOT / "data" / "ride.json")
        command.add_argument("--config", type=Path, default=ROOT / "data" / "map_config.json")
        command.add_argument("--base-url", default="http://127.0.0.1:8765")
        command.add_argument("--api-key", default="practice-map-key")
        command.add_argument("--timeout", type=float, default=3.0)
        if name in {"base", "route"}:
            command.add_argument("--output", type=Path, default=ROOT / "artifacts" / f"{name}.png")
        if name == "route":
            command.add_argument("--segments-per-path", type=int, default=10)
    args = parser.parse_args(argv)

    try:
        if args.command == "doctor":
            for path in (args.input, args.config):
                with path.open(encoding="utf-8") as handle:
                    json.load(handle)
            response = requests.get(args.base_url.rstrip("/") + "/health", timeout=3)
            response.raise_for_status()
            if response.json().get("service") != "practice-staticmap":
                raise ValueError("The endpoint is not the practice map service.")
            print("OK: Python, requests, both JSON inputs, and local HTTP service.")
            return 0

        if args.command == "inspect":
            positions = load_positions(args.input)
            print(f"Positions: {len(positions)}")
            print(json.dumps(positions[:10], indent=2))
            return 0

        with args.config.open(encoding="utf-8") as handle:
            config = json.load(handle)
        if args.command == "base":
            payload = base_map_payload(config)
        else:
            positions = load_positions(args.input)
            payload = build_route_payload(positions, config, args.segments_per_path)
        with MapClient(args.base_url, args.api_key, args.timeout) as client:
            image = client.render(payload)
        output = save_image(image, args.output)
        print(f"Saved {len(image)} bytes to {output}")
        return 0
    except (NotImplementedError, MapAPIError, OSError, ValueError, requests.RequestException) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
