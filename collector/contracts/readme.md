# Collector Contracts

This directory defines the **language** of the Collector cell.

Every capability that interacts with Collector speaks this language.

---

## Philosophy

- Nothing here knows about implementation.
- Nothing here knows about consumers.
- Nothing here knows about domains.
- Nothing here evolves independently.

The contracts are stable.

The capabilities evolve.

---

## Concepts (to be defined)

- **Document** — The raw unit of collected information.
- **RawDocument** — Unprocessed retrieved material.
- **ParsedDocument** — Extracted structure.
- **NormalizedDocument** — Transformed into a common representation.
- **ValidatedDocument** — Verified against defined rules.
- **KnowledgeRecord** — Validated information ready for storage.
- **Connector** — Establishes communication with a Source.
- **Fetcher** — Retrieves information.
- **Parser** — Extracts structure.
- **Normalizer** — Transforms data.
- **Validator** — Verifies constraints.
- **Storage** — Persists Knowledge Records.
- **Workflow** — Orchestrates capabilities.
- **Run** — One identifiable execution.

---

## Evolution

These definitions are **provisional**.

They will evolve only when evidence from real execution proves they are inadequate or incomplete.

That is CEP-015 in practice.

---

## The Contract Promise

> **If you speak this language, you can be part of Collector.**
>
> **If you don't, you can't.**

That is the only rule.
