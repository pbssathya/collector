"""
Collect historical Keralam Lottery results.

This script collects results from a range of draw serials
and stores them in the Knowledge Store.
"""

import time
from datetime import datetime
from typing import Optional

from collector.connectors.keralam_lottery import KeralamLotteryConnector
from collector.parsers.keralam_result import KeralamResultParser
from collector.storage.sqlite_store import SQLiteKnowledgeStore
from collector.storage.knowledge_store import KnowledgeRecord


class HistoricalCollector:
    """Collects historical lottery results."""

    def __init__(self, db_path: str = "knowledge.db"):
        self.connector = KeralamLotteryConnector()
        self.parser = KeralamResultParser()
        self.store = SQLiteKnowledgeStore(db_path)
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

    def collect_range(self, start_serial: int, end_serial: int, delay: float = 0.5):
        """
        Collect results from a range of serials.

        Args:
            start_serial: First serial to collect.
            end_serial: Last serial to collect.
            delay: Delay between requests (seconds).
        """
        print(f"📊 Collecting serials {start_serial} to {end_serial}")
        print(f"   Total: {end_serial - start_serial + 1} draws")
        print("-" * 40)

        for serial in range(start_serial, end_serial + 1):
            self._collect_one(serial)
            time.sleep(delay)

        self._print_summary()

    def collect_from(self, start_serial: int, count: int, delay: float = 0.5):
        """
        Collect a specific number of results starting from a serial.

        Args:
            start_serial: First serial to collect.
            count: Number of results to collect.
            delay: Delay between requests (seconds).
        """
        end_serial = start_serial + count - 1
        self.collect_range(start_serial, end_serial, delay)

    def _collect_one(self, serial: int):
        """Collect a single draw and store it."""
        self.stats["total"] += 1

        # Check if already collected
        existing = self.store.query(source=f"keralam_lottery_{serial}", limit=1)
        if existing:
            print(f"⏭️  Serial {serial}: Already collected")
            self.stats["skipped"] += 1
            return

        try:
            # Fetch the document
            doc = self.connector.fetch_draw(serial)

            if not doc or not doc.content:
                print(f"❌ Serial {serial}: No content")
                self.stats["failed"] += 1
                return

            # Parse the result
            result = self.parser.parse(doc.content)

            if not result:
                print(f"❌ Serial {serial}: Failed to parse")
                self.stats["failed"] += 1
                return

            # Create a KnowledgeRecord
            record = KnowledgeRecord(
                source=f"keralam_lottery_{serial}",
                collected_at=datetime.now(),
                raw_data=doc.content,
                parsed_data={
                    "lottery_name": result.lottery_name,
                    "draw_date": result.draw_date,
                    "first_prize": result.first_prize,
                    "first_prize_location": result.first_prize_location,
                    "second_prize": result.second_prize,
                    "second_prize_location": result.second_prize_location,
                    "third_prize": result.third_prize,
                    "third_prize_location": result.third_prize_location,
                    "consolation_prizes": result.consolation_prizes,
                    "fourth_prize_numbers": result.fourth_prize_numbers,
                    "fifth_prize_numbers": result.fifth_prize_numbers,
                    "sixth_prize_numbers": result.sixth_prize_numbers,
                    "seventh_prize_numbers": result.seventh_prize_numbers,
                    "eighth_prize_numbers": result.eighth_prize_numbers,
                    "ninth_prize_numbers": result.ninth_prize_numbers,
                },
                metadata={
                    "serial": serial,
                    "fetcher": "HTTPFetcher",
                    "parser": "KeralamResultParser",
                }
            )

            # Save to the Knowledge Store
            record_id = self.store.save(record)
            print(f"✅ Serial {serial}: Saved (ID: {record_id})")
            self.stats["success"] += 1

        except Exception as e:
            print(f"❌ Serial {serial}: Error - {e}")
            self.stats["failed"] += 1

    def _print_summary(self):
        """Print collection summary."""
        print("-" * 40)
        print("📊 Collection Summary")
        print(f"   Total:    {self.stats['total']}")
        print(f"   Success:  {self.stats['success']} ✅")
        print(f"   Failed:   {self.stats['failed']} ❌")
        print(f"   Skipped:  {self.stats['skipped']} ⏭️")
        print(f"   Stored:   {self.store.count()} total records")


def main():
    """Main entry point."""
    import sys

    collector = HistoricalCollector()

    if len(sys.argv) == 1:
        print("Usage:")
        print("  python -m collector.scripts.collect_historical <start_serial> <count>")
        print()
        print("Example:")
        print("  python -m collector.scripts.collect_historical 75352 10")
        return

    if len(sys.argv) >= 3:
        start = int(sys.argv[1])
        count = int(sys.argv[2])
        collector.collect_from(start, count)
    else:
        print("❌ Please provide start serial and count.")


if __name__ == "__main__":
    main()
