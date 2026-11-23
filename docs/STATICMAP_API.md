# StaticMap API: local practice contract

This document specifies our mock service, not a public Stripe API.

## Connection

Default base URL: `http://127.0.0.1:8765`

Development key: `practice-map-key`

The key is deliberately public and works only with the local exercise. Never provide a real Stripe or map-provider credential.

## Health

`GET /health` requires no authentication. Returns JSON:

```json
{"status": "ok", "service": "practice-staticmap"}
```

## Render

`POST /map.png`

Required headers:

```text
Authorization: Bearer practice-map-key
Content-Type: application/json
Accept: image/png
```

The body must be a JSON object. Form-encoded fields and a JSON-encoded string containing JSON are not accepted.

### Base-map fields

```json
{
  "center": {"lat": 47.579, "lon": -122.31},
  "width": 400,
  "height": 600,
  "zoom": 13
}
```

- `center`: geographic coordinate object with finite numeric `lat` and `lon` in their usual ranges.
- `width`, `height`: integers from 100 through 1200.
- `zoom`: integer from 1 through 20.
- Boolean values do not qualify as numbers or integers in this contract.

### Optional overlays

`markers` and `paths` default to empty arrays.

```json
{
  "markers": [
    {
      "color": "white",
      "label": "Start",
      "coord": {"lat": 47.580, "lon": -122.320}
    }
  ],
  "paths": [
    {
      "color": "blue",
      "positions": [
        {"lat": 47.580, "lon": -122.320},
        {"lat": 47.581, "lon": -122.319}
      ]
    }
  ]
}
```

- Marker colors: `white`, `blue`, or `brown`.
- Marker labels: `Start` or `Stripe`.
- Path colors: `blue` or `brown`.
- Every path must contain at least two valid coordinate objects.
- At most 20 markers, 1000 paths, and 20000 total path positions.
- Unknown fields are rejected, including extra fields inside coordinates or overlays.
- The request body cannot exceed 2 MB.

The service validates request shape and draws exactly what it receives. It does not enforce your ride-grouping or marker-placement requirements; the client acceptance tests do that.

### Success

```text
HTTP/1.0 200 OK
Content-Type: image/png
X-Request-Id: <request identifier>
```

The body contains PNG bytes, not JSON. No additional download request is needed. The local image is a synthetic grid and a simple geographic projection; it is not suitable for navigation.

### Errors

Errors return JSON, for example:

```json
{"error": {"code": "invalid_request", "message": "width must be an integer from 100 to 1200"}}
```

| Status | Meaning |
| --- | --- |
| 400 | Invalid JSON or map parameters |
| 401 | Missing or incorrect bearer key |
| 404 | Unknown endpoint |
| 413 | Request exceeds 2 MB |
| 415 | Body is not declared as JSON, or PNG is not accepted |

For this exercise, fail on errors rather than retrying. Set a positive finite request timeout. Preserve useful error context in `MapAPIError`, and do not mistake an error body for an image.

## Local diagnostics

`GET /__requests` returns the last 100 parsed render request bodies in a JSON
`requests` array. It is a local development aid for inspecting what your client
actually sent, not an endpoint you need for the implementation. It does not
include authorization headers.
