# CiviSentry 360

AI-powered construction safety and site intelligence prototype for REC-AIX 2026.

## Run

Open `civisentry360.html` directly in a browser. It is fully offline and requires no installation.

## Files

- `civisentry360.html` — interactive dashboard
- `civisentry_simulated_data.csv` — 48-row synthetic telemetry dataset
- `CiviSentry360_README.md` — project notes

## Demo scope

The application demonstrates controlled synthetic scenarios: normal work, heat stress and possible fall. It includes a risk engine, site-zone intelligence, RAG evidence presentation, English/Tamil safety recommendations and what-if simulation.

## Data integrity

The CSV is synthetic and is not represented as field-measured or medically validated data. It is intended to validate the product workflow before live hardware acquisition and site testing.

## LLM/RAG integration

The current offline demo presents grounded retrieval evidence and a deterministic fallback response. A production integration can pass the selected event, risk features and retrieved safety passage to an LLM through a server-side API. The LLM should explain and localize the recommendation; immediate critical-event detection should remain local and deterministic.

## Presentation title

**CiviSentry 360: A Multimodal AI Construction Safety and Site Intelligence Platform for Tamil Nadu**
