# 🌿 Collector

> *"I am the Collector. I am a stable cell. I perform my duty."*

Collector is a domain-independent, open-source data collection cell.

It exists to connect, collect, parse, normalize, validate, store, update, and report what happened during collection. It does not analyse, predict, recommend, or decide for consumers.

## The Root Evolves. The Collector Remains.

Collector's duty is stable. It does not reinterpret its mission or decide how the ecosystem should evolve. The Root observes evidence from real execution and decides when the ecosystem needs new or changed capability.

## Core Principles

- **Architectural Independence:** Collector does not know its consumers.
- **Faithful Preservation:** Canonical collected material is preserved completely.
- **Explainability:** Execution facts and events are traceable.
- **No Judgment:** Collector does not analyse, predict, recommend, or decide.
- **Replaceability:** Connectors and supporting layers can change without consumers depending on collection internals.
- **Configuration over Hardcoding:** Domain-specific behaviour belongs outside reusable core capability.

## Knowledge Store

The Knowledge Store is the contract between Collector and its consumers. Collector may persist collected and structured material when requested, while consumers remain unaware of how that material was obtained.

## Status

✅ **Collector 1.0.0 — Stable Cell**

The first stable Collector cell includes:

- domain registry and connector contract
- HTTP retrieval with redirect and execution observations
- raw `Document` preservation
- parsing support through domain connectors
- SQLite knowledge storage
- standardized Collector report contract
- automated test verification across supported Python versions

Future domains should extend Collector through connectors and configuration rather than architectural rewrites.

## Development

Install development dependencies:

```bash
python -m pip install -e '.[dev]'
```

Run tests:

```bash
python -m pytest -q
```

Collector currently supports Python 3.10, 3.11, and 3.12 in CI.
