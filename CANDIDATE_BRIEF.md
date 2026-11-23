# Candidate brief

You are joining a small team that builds downloadable previews of recorded bicycle rides. A CLI already exists, but its GeoJSON reader and static-map integration are unfinished. Implement the missing pieces using Python, `json`, and `requests`.

There are exactly two parts. Production-readiness questions at the end are discussion prompts, not additional implementation tasks.

## Provided files

- `data/ride.json`: a synthetic recorded ride, with 35 coordinate samples.
- `data/map_config.json`: map settings to send to the rendering service.
- `app.py`: existing commands and orchestration.
- `bikemap/`: candidate code and error classes.
- `mock_server.py`: a working local map API. Treat this as an external dependency.
- `docs/STATICMAP_API.md`: its contract.
- `tests/`: public acceptance checks, including real HTTP calls.

Only the three modules containing TODOs need editing. You may add helpers and your own tests. You may consult Python and Requests documentation.

## Part 1: Read the ride and integrate the base-map endpoint

Implement `load_positions`, `MapClient.render`, and `save_image`.

### Read the supplied ride

`load_positions(path)` returns a list of coordinate dictionaries in the original track order. The source format is GeoJSON: coordinate arrays are longitude first. The map service's coordinate objects use named `lat` and `lon` fields.

For this exercise:

- The root must be a `FeatureCollection`.
- The first feature contains the ride and must have a `LineString` geometry.
- Other features are ignored.
- There must be at least two coordinates.
- Each coordinate has two or three numeric components; ignore the optional third (altitude).
- Longitude must be in `[-180, 180]` and latitude in `[-90, 90]`.
- The first two components must be finite numbers, not booleans.
- Raise the provided `TrackFormatError` for invalid JSON or an invalid track structure. Error wording is up to you.
- A missing input file may raise `FileNotFoundError`.

Run `python app.py inspect`. The CLI should print the total number of positions and the first ten converted positions. It must not call the map API.

### Request and save a base map

Run `python app.py base --output artifacts/base.png`.

The CLI already loads the config file and calls your client. Read the API docs to implement the request, authentication, response handling, and finite timeout. The successful response is an image; preserve its bytes exactly.

Raise the provided `MapAPIError` for HTTP errors, transport errors, or an unexpected response media type. Its `status_code` should be the actual HTTP status for an HTTP response, or `None` for a transport error. A failed API call must not create or replace an output image.

`save_image` receives successful bytes and an output path. Create missing parent directories, write the bytes, and return the resulting `Path`.

Check: `python check.py --part 1`.

## Part 2: Draw the ride

Implement `build_route_payload(positions, config, segments_per_path=10)` and run `python app.py route`.

Keep all the configured map settings and add:

- A white marker labeled `Start` at the first position.
- A blue marker labeled `Stripe` at the last position.
- Paths covering the entire ride, initially blue and then alternating brown, blue, brown, and so on.
- Each path covers up to `segments_per_path` consecutive line segments. A segment connects two adjacent positions.
- Adjacent paths share their boundary position so the route has no gaps.
- Preserve the final incomplete group; do not produce an empty or single-position path.

For example, a ride with 24 segments and a group size of 10 needs paths covering 10, 10, and 4 segments. The supplied ride has 34 segments.

The function must not mutate `positions` or `config`. Raise `ValueError` when fewer than two positions are supplied or the group size is not a positive integer. Use the same HTTP client and save helper from part 1.

Check: `python check.py --part 2`, then run all checks again. Open the final PNG manually and verify that it contains a continuous route and both markers.

## Discussion after the implementation

Be ready to explain:

- How you would diagnose a 400 response from the service.
- Which logs and metrics would help in production without dumping private route data or credentials.
- Which requests could be retried safely and how you would bound retries and handle rate limits.
- How you would test without calling a paid external provider.
- How large inputs, output-file failures, or a much slower service would change your design.

There is no requirement to build a web service, implement retry machinery, or add concurrency in this mock.
