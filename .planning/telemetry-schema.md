# Telemetry Schema — Normalized Run Record

Purpose: Define a compact, reviewer-friendly telemetry schema for every inference run in the demo. The schema is intentionally small and focused on reproducibility and inspectability for interview/demo use.

## Record structure (json)

- id: string (UUID) — unique run identifier
- timestamp: string (ISO 8601) — run start time
- strategy: string — routing strategy selected (e.g., "priority", "round_robin", "latency")
- provider: string — provider or model key used for the final result
- model: string | null — model identifier if available
- latency_ms: number | null — observed end-to-end latency in milliseconds
- tokens: integer | null — request/response tokens when available
- cost: number | null — estimated cost when available
- fallback_attempts: array of {provider: string, reason: string | null, latency_ms: number | null}
- trace_id: string | null — optional Langfuse trace id
- raw_response: object | null — raw provider response when available and needed for inspectability

## Example

{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2026-08-19T17:00:00Z",
  "strategy": "latency",
  "provider": "openrouter/model-x",
  "model": "gpt-4o-mini",
  "latency_ms": 312.4,
  "tokens": 142,
  "cost": 0.0024,
  "fallback_attempts": [
    {"provider": "openrouter/model-x", "reason": null, "latency_ms": 312.4}
  ],
  "trace_id": null,
  "raw_response": {"text": "..."}
}

## Notes

- Fields that may not be available from all providers are nullable; the UI should display "Unavailable" when a field is null.
- For privacy and security, raw_response should only be stored if the demo user/maintainer consents; otherwise, store minimal inspection evidence.
- Langfuse traces are optional and controlled via config readiness checks.
