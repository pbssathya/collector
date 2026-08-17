"""
Generic Collector CLI

Collects data from any domain.
"""

import sys
import json
import argparse
from datetime import datetime
from typing import Optional

from collector.storage.sqlite_store import SQLiteKnowledgeStore
from collector.storage.knowledge_store import KnowledgeRecord
from collector.domains.registry import DomainRegistry


def collect_domain(domain: str, source: str, store: bool = True) -> Optional[dict]:
    """Collect data from a domain."""
    registry = DomainRegistry()
    connector = registry.get_connector(domain)
    
    if not connector:
        print(f"❌ Unknown domain: {domain}")
        print(f"   Available domains: {', '.join(registry.list_domains())}")
        return None
    
    print(f"🔍 Collecting from domain: {domain}")
    print(f"   Source: {source}")
    
    try:
        doc = connector.retrieve(source)
        
        if not doc or not doc.content:
            print("❌ No content received")
            return None
        
        print(f"   Fetched: {len(doc.content)} bytes")
        
        parsed_data = None
        if hasattr(connector, "parse"):
            parsed_data = connector.parse(doc.content)
            if parsed_data:
                print(f"✅ Parsed successfully")
        
        if store and parsed_data:
            store_instance = SQLiteKnowledgeStore()
            record = KnowledgeRecord(
                source=f"{domain}_{source}",
                collected_at=datetime.now(),
                raw_data=doc.content,
                parsed_data=parsed_data,
                metadata={
                    "domain": domain,
                    "source": source,
                    "fetcher": "HTTPFetcher",
                    "connector": connector.__class__.__name__,
                }
            )
            record_id = store_instance.save(record)
            print(f"   Stored: ID {record_id}")
        
        return parsed_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


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
    parser = argparse.ArgumentParser(
        description="Collect data from any domain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m collector.collect keralam 75352
  python -m collector.collect keralam --latest
  python -m collector.collect keralam --range 75346 75352
  python -m collector.collect weather london
  python -m collector.list
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect data from a domain")
    collect_parser.add_argument("domain", help="Domain name (e.g., keralam, weather)")
    collect_parser.add_argument("source", nargs="?", help="Source identifier (e.g., serial number)")
    collect_parser.add_argument("--latest", action="store_true", help="Collect the latest source")
    collect_parser.add_argument("--range", nargs=2, metavar=("START", "END"), help="Collect a range of sources")
    collect_parser.add_argument("--no-store", action="store_true", help="Don't store the result")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available domains")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_domains()
        return 0
    
    elif args.command == "collect":
        if not args.source and not args.latest and not args.range:
            print("❌ Please provide a source, --latest, or --range")
            return 1
        
        # Handle latest
        if args.latest:
            # TODO: Implement latest discovery
            print("⚠️  --latest not yet implemented")
            return 1
        
        # Handle range
        if args.range:
            start = int(args.range[0])
            end = int(args.range[1])
            print(f"📊 Collecting range {start} to {end}")
            # TODO: Implement range collection
            return 1
        
        # Handle single source
        result = collect_domain(args.domain, args.source, not args.no_store)
        if result:
            print("\n📊 Result:")
            print(json.dumps(result, indent=2, default=str))
            return 0
        else:
            return 1
    
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
