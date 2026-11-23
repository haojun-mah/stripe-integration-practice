# Interviewer notes -- spoilers

Keep this directory closed during the mock. `solution.py` is an isolated answer key; it never replaces the candidate modules.

Verify the exercise itself:

```powershell
python check.py --reference --part all
```

The normal check command never uses the reference implementation.

## Review focus

- Candidate inspects both JSON documents and the API contract before guessing fields.
- Part 1 keeps geographic coordinate order straight, sends JSON rather than form data, authenticates, passes a timeout, checks errors, and saves binary bytes.
- Part 2 adds overlays without breaking the earlier base-map command.
- The supplied 35-point ride has 34 segments. With group size 10, expected path point counts are 11, 11, 11, and 5, with colors blue, brown, blue, brown.
- Neighboring groups share one coordinate. The endpoint of one group is the start of the next.
- The provided labels and marker coordinates matter, not only whether the API accepts the body.
- Candidate runs both original-input checks and short/exact-boundary/remainder cases.
- The brief has exactly two implementation parts. Do not quietly add retry, pagination, webhook, or database tasks.

## Suggested discussion

Ask how to handle the service returning 400, 429, 503, a timeout, or a non-image success. Rendering is a read-like POST in this synthetic service, but production retry safety must come from the provider's contract. Ask about bounded retries, redacted diagnostics, request IDs, quotas, large tracks, secure configuration, and atomic output writes. These are discussion topics, not requirements for the timed implementation.

The PNG renderer is intentionally schematic. Do not grade candidates on graphic fidelity or geographic projection.
