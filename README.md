# BikeMap: a one-hour Python integration round

Build a downloadable map of a bicycle ride using `json` and `requests`.

**Edit only `exercise.py`. There are two functions to complete.** The local map service and command-line wiring are provided. You may add helpers and consult library documentation.

## Setup

Python 3.10+:

```powershell
git clone https://github.com/haojun-mah/stripe-integration-practice.git
cd stripe-integration-practice
python -m pip install -r requirements.txt
python check.py --part setup
```

Start the provided service in a separate terminal:

```powershell
python -m service.server
```

Only read this page, `exercise.py`, and the two JSON inputs. You do not need to read or change `service/` or the test runner.

## Part 1 -- Request a map (about 15 minutes)

Implement `render_map(payload, output_path, base_url=BASE_URL)` in `exercise.py`.

1. Send `payload` to the map API documented below.
2. Use a positive finite request timeout.
3. If the response is an HTTP error, let `requests.HTTPError` propagate before writing any file. A transport error may propagate normally too.
4. Save successful response bytes using the provided `write_png` helper and return its `Path`.

The CLI loads `data/map_config.json` for you:

```powershell
python exercise.py base
python check.py --part 1
```

Open `artifacts/base.png`. It should contain a background grid.

## Part 2 -- Add the ride (about 25 minutes)

Implement `render_ride(ride_path, config_path, output_path, base_url=BASE_URL)`.

1. Read the two JSON files. `ride.json` is GeoJSON; the route is at `features[0].geometry.coordinates`. Each pair is `[longitude, latitude]`, in track order. The config contains the base-map settings.
2. Convert the coordinates to the API's `{"lat": ..., "lon": ...}` objects.
3. Add a white `Start` marker at the first point and a blue `Stripe` marker at the last point.
4. Add paths covering ten consecutive **segments** each, alternating blue, brown, blue, brown, starting with blue. Neighboring paths share their boundary point. Keep a shorter final group.
5. Reuse `render_map` to request the image, save it, and return its `Path`.

A segment connects two adjacent points. All input files are valid, have the shown shape, and contain at least two two-number coordinates. No general GeoJSON validation is required.

```powershell
python exercise.py ride
python check.py --part 2
python check.py --part all
```

Open `artifacts/ride.png`. Check both markers and continuity where the color changes. Tests cover short rides, exact group boundaries, and a remainder.

## API quick reference

**POST** `http://127.0.0.1:8765/map.png`

Send a JSON object and the provided `API_HEADERS` constant from `exercise.py`.

```json
{
  "center": {"lat": 47.579, "lon": -122.31},
  "width": 400,
  "height": 600,
  "zoom": 13,
  "markers": [
    {"color": "white", "label": "Start", "coord": {"lat": 47.57, "lon": -122.32}}
  ],
  "paths": [
    {"color": "blue", "positions": [
      {"lat": 47.57, "lon": -122.32},
      {"lat": 47.58, "lon": -122.31}
    ]}
  ]
}
```

`markers` and `paths` are optional for a base map. Success is HTTP 200 with **PNG bytes**, not JSON. Errors are HTTP 4xx/5xx with an error body; do not save them as images. The development key is already supplied in `API_HEADERS` and requires no account.

## Finish

Allow 5 minutes to read and 15 minutes to test and discuss: What would you add for production? How would you diagnose a 400 or handle a timeout?

The nine tests start their own local service, so checks do not need the manually running server. Setup checks pass immediately; implementation checks fail until the two TODOs are completed.

This is original practice material inspired by reported Stripe integration exercises, not Stripe's actual repository. [Source notes](docs/SOURCES.md).
