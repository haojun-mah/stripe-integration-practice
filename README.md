# Stripe integration practice: BikeMap

A small Python repo for a 60-minute integration mock. There are **two parts**, **two JSON input files**, and four deliberately unfinished functions. You will read an existing project, consult an API contract, call a real local HTTP service with `requests`, and write a PNG.

This is an original practice adaptation, not a copy of Stripe's private repo. The two-part organization follows the context you provided. Public reports on Prachub and 1Point3Acres supply the BikeMap theme; the local service, fixtures, tests, and exact contract are ours. See [sources](docs/SOURCES.md).

## Start here

Python 3.10+ is required. In PowerShell:

```powershell
git clone https://github.com/haojun-mah/stripe-integration-practice.git
cd stripe-integration-practice
python -m pip install -r requirements.txt
python mock_server.py
```

Keep that terminal running. In a second terminal, in the same directory:

```powershell
python app.py doctor
python check.py --part setup
```

Both should pass before you start. No account, paid service, or real API key is needed. The mock service listens on `127.0.0.1:8765` by default. Use Ctrl+C to stop it.

## Your round

Read [the candidate brief](CANDIDATE_BRIEF.md), then [the API documentation](docs/STATICMAP_API.md).

Implement these functions, marked `TODO`:

| File | Your responsibility |
| --- | --- |
| `bikemap/track.py` | Read GeoJSON and convert coordinates |
| `bikemap/client.py` | Send the documented HTTP request and return image bytes |
| `bikemap/rendering.py` | Save bytes; build the route-overlay request |

The existing CLI and mock server are provided infrastructure. You do not need to implement graphics or change the server.

```powershell
python app.py inspect
python app.py base --output artifacts/base.png
python check.py --part 1
python app.py route --output artifacts/route.png
python check.py --part 2
python check.py --part all
```

Open your output PNGs manually after each part. The server draws a synthetic local grid with the route, not real map tiles.

Part checks start their own server on an unused local port. They do not depend on your manually running server. Candidate checks are **expected to fail until you implement the TODOs**; setup checks should already pass.

## Reading order

1. `CANDIDATE_BRIEF.md`
2. `app.py` to follow the existing flow
3. The two files in `data/`
4. `docs/STATICMAP_API.md`
5. The three candidate modules above

Suggested timing: 5 minutes reading, 20 minutes part 1, 25 minutes part 2, 10 minutes validation and discussion. These are practice timings, not an official Stripe format.

The `interviewer/` folder contains spoilers: a reference implementation and reviewer notes. Leave it closed while practicing.

If port 8765 is busy:

```powershell
python mock_server.py --port 8766
python app.py doctor --base-url http://127.0.0.1:8766
python app.py route --base-url http://127.0.0.1:8766
```
