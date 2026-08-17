# Collector Report Contract

The Collector produces a standardized report that any leaf can consume.

## Version

1.0.0

## Format

The report is a JSON object with the following structure:

```json
{
  "report_version": "1.0.0",
  "request": {
    "domain_path": "games/chance/lottery/kerala",
    "source": "75352",
    "requested_at": "2026-08-18T10:30:00Z",
    "requester": "nokku"
  },
  "data": {
    "raw": "...",
    "parsed": { ... },
    "format": "pdf"
  },
  "execution": {
    "status": "success",
    "duration_ms": 1234,
    "events": [
      {
        "type": "redirect",
        "from": "http://old.url",
        "to": "http://new.url",
        "timestamp": "2026-08-18T10:30:01Z"
      }
    ],
    "connector_used": "Connector"
  },
  "metadata": {
    "collected_at": "2026-08-18T10:30:02Z",
    "source_url": "http://result.keralalotteries.com/viewlotisresult.php?drawserial=75352",
    "content_type": "application/pdf",
    "size_bytes": 87147
  },
  "provenance": {
    "run_id": "run_123456",
    "collector_version": "0.1.0",
    "domain_version": "1.0.0"
  }
}
