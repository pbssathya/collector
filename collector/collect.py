"""
Generic Collector CLI

Collects data from any domain and returns a standardized report.
"""

import sys
import json
import uuid
import time
from datetime import datetime
from typing import Optional

from collector.storage.sqlite_store import SQLiteKnowledgeStore
from collector.storage.knowledge_store import KnowledgeRecord
from collector.domains.registry import DomainRegistry


def collect(domain_path: str, source: str, store: bool = True, requester: Optional[str] = None) -> Optional[dict]:
    """
    Collect data from a domain and return a standardized report.

    Args:
        domain_path: The domain path (e.g., 'games/chance/lottery/kerala')
        source: The source identifier
        store: Whether to store the result
        requester: Optional identifier of the requesting leaf

    Returns:
        A standardized CollectorReport dict, or None if collection failed.
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    start_time = time.time()
    requested_at = datetime.now().isoformat() + "Z"

    # Get the connector
    registry = DomainRegistry()
    connector = registry.get_connector(domain_path)

    if not connector:
        return {
            "report_version": "1.0.0",
            "request": {
                "domain_path": domain_path,
                "source": source,
                "requested_at": requested_at,
                "requester": requester
            },
            "data": {
                "raw": None,
                "parsed": None,
                "format": None
            },
            "execution": {
                "status": "failed",
                "duration_ms": (time.time() - start_time) * 1000,
                "events": [
                    {
                        "type": "domain_not_found",
                        "message": f"Unknown domain: {domain_path}",
                        "timestamp": datetime.now().isoformat() + "Z"
                    }
                ],
                "connector_used": None
            },
            "metadata": {
                "collected_at": datetime.now().isoformat() + "Z",
                "source_url": None,
                "content_type": None,
                "size_bytes": 0
            },
            "provenance": {
                "run_id": run_id,
                "collector_version": "1.0.0",
                "domain_version": "1.0.0"
            }
        }

    print(f"🔍 Collecting from domain: {domain_path}")
    print(f"   Source: {source}")

    events = []
    doc = None

    try:
        # Fetch the document
        fetch_start = time.time()
        doc = connector.retrieve(source)
        fetch_duration = (time.time() - fetch_start) * 1000

        if not doc:
            events.append({
                "type": "fetch_failed",
                "message": "No document returned",
                "timestamp": datetime.now().isoformat() + "Z"
            })
            return _create_failed_report(domain_path, source, requested_at, requester, run_id, events)

        if doc.error:
            events.append({
                "type": "fetch_error",
                "message": doc.error,
                "timestamp": datetime.now().isoformat() + "Z"
            })
            return _create_failed_report(domain_path, source, requested_at, requester, run_id, events, error=doc.error)

        if not doc.content:
            events.append({
                "type": "empty_content",
                "message": "Document has no content",
                "timestamp": datetime.now().isoformat() + "Z"
            })
            return _create_failed_report(domain_path, source, requested_at, requester, run_id, events)

        print(f"   Fetched: {len(doc.content)} bytes")

        # Parse the document
        parsed_data = None
        parse_status = "not_parsed"
        if hasattr(connector, "parse"):
            try:
                parse_start = time.time()
                parsed_data = connector.parse(doc.content)
                parse_duration = (time.time() - parse_start) * 1000
                if parsed_data:
                    parse_status = "success"
                    print("✅ Parsed successfully")
                else:
                    parse_status = "failed"
                    events.append({
                        "type": "parse_failed",
                        "message": "Parser returned None",
                        "timestamp": datetime.now().isoformat() + "Z"
                    })
            except Exception as e:
                parse_status = "error"
                events.append({
                    "type": "parse_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat() + "Z"
                })

        # Store the result
        store_status = "not_stored"
        record_id = None
        if store and parsed_data:
            try:
                store_instance = SQLiteKnowledgeStore()
                record = KnowledgeRecord(
                    source=f"{domain_path}_{source}",
                    collected_at=datetime.now(),
                    raw_data=doc.content,
                    parsed_data=parsed_data,
                    metadata={
                        "domain": domain_path,
                        "source": source,
                        "run_id": run_id,
                        "requester": requester,
                        "connector": connector.__class__.__name__,
                    }
                )
                record_id = store_instance.save(record)
                store_status = "success"
                print(f"   Stored: ID {record_id}")
            except Exception as e:
                store_status = "failed"
                events.append({
                    "type": "store_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat() + "Z"
                })

        # Build the report. Raw material is canonical and complete here;
        # display layers may choose their own abbreviated representation.
        report = {
            "report_version": "1.0.0",
            "request": {
                "domain_path": domain_path,
                "source": source,
                "requested_at": requested_at,
                "requester": requester
            },
            "data": {
                "raw": doc.content,
                "parsed": parsed_data,
                "format": doc.content_type or "unknown"
            },
            "execution": {
                "status": "success" if parsed_data else "partial",
                "duration_ms": (time.time() - start_time) * 1000,
                "events": events,
                "connector_used": connector.__class__.__name__
            },
            "metadata": {
                "collected_at": datetime.now().isoformat() + "Z",
                "source_url": doc.source_url if hasattr(doc, "source_url") else None,
                "content_type": doc.content_type,
                "size_bytes": len(doc.content) if doc.content else 0
            },
            "provenance": {
                "run_id": run_id,
                "collector_version": "1.0.0",
                "domain_version": "1.0.0"
            }
        }

        # Add record_id if stored
        if record_id:
            report["metadata"]["record_id"] = record_id

        return report

    except Exception as e:
        events.append({
            "type": "collector_error",
            "message": str(e),
            "timestamp": datetime.now().isoformat() + "Z"
        })
        return _create_failed_report(domain_path, source, requested_at, requester, run_id, events, error=str(e))


def _create_failed_report(domain_path, source, requested_at, requester, run_id, events, error=None):
    """Create a failed report."""
    return {
        "report_version": "1.0.0",
        "request": {
            "domain_path": domain_path,
            "source": source,
            "requested_at": requested_at,
            "requester": requester
        },
        "data": {
            "raw": None,
            "parsed": None,
            "format": None
        },
        "execution": {
            "status": "failed",
            "duration_ms": 0,
            "events": events,
            "connector_used": None
        },
        "metadata": {
            "collected_at": datetime.now().isoformat() + "Z",
            "source_url": None,
            "content_type": None,
            "size_bytes": 0
        },
        "provenance": {
            "run_id": run_id,
            "collector_version": "1.0.0",
            "domain_version": "1.0.0"
        }
    }


def list_domains():
    """List all available domains."""
    registry = DomainRegistry()
    domains = registry.list_domains_with_info()

    if not domains:
        print("No domains found.")
        return

    print("📋 Available Domains:")
    for name, info in domains.items():
        print(f"  - {name}: {info['doc'][:60]}...")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect data from any domain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m collector.collect collect games/chance/lottery/kerala 75352
  python -m collector.collect list
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect data from a domain")
    collect_parser.add_argument("domain", help="Domain path (e.g., games/chance/lottery/kerala)")
    collect_parser.add_argument("source", help="Source identifier (e.g., serial number)")
    collect_parser.add_argument("--requester", help="Identifier of the requesting leaf")
    collect_parser.add_argument("--no-store", action="store_true", help="Don't store the result")

    # List command
    subparsers.add_parser("list", help="List available domains")

    args = parser.parse_args()

    if args.command == "list":
        list_domains()
        return 0

    elif args.command == "collect":
        result = collect(args.domain, args.source, not args.no_store, args.requester)
        if result:
            print("\n📊 Report:")
            print(json.dumps(result, indent=2, default=str))
            return 0 if result["execution"]["status"] != "failed" else 1
        else:
            return 1

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
