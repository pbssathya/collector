"""
Test the Knowledge Store with a collected result.
"""

from collector.connectors.keralam_lottery import KeralamLotteryConnector
from collector.parsers.keralam_result import KeralamResultParser
from collector.storage.sqlite_store import SQLiteKnowledgeStore
from collector.storage.knowledge_store import KnowledgeRecord
from datetime import datetime

# Initialize
connector = KeralamLotteryConnector()
parser = KeralamResultParser()
store = SQLiteKnowledgeStore("knowledge.db")

# Fetch the latest result
SERIAL = 75352
doc = connector.fetch_draw(SERIAL)

if doc and doc.content:
    result = parser.parse(doc.content)

    if result:
        # Create a KnowledgeRecord
        record = KnowledgeRecord(
            source=f"keralam_lottery_{SERIAL}",
            collected_at=datetime.now(),
            raw_data=doc.content,  # The PDF bytes
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
                "serial": SERIAL,
                "fetcher": "HTTPFetcher",
                "parser": "KeralamResultParser",
            }
        )

        # Save to the Knowledge Store
        record_id = store.save(record)
        print(f"✅ Record saved with ID: {record_id}")

        # Retrieve and verify
        retrieved = store.get(record_id)
        if retrieved:
            print(f"✅ Retrieved record: {retrieved.id}")
            print(f"   Source: {retrieved.source}")
            print(f"   Collected at: {retrieved.collected_at}")
            print(f"   Lottery: {retrieved.parsed_data['lottery_name']}")
            print(f"   1st Prize: {retrieved.parsed_data['first_prize']}")

        # Show total count
        print(f"\n📊 Total records in store: {store.count()}")

        # Show recent records
        print("\n📋 Recent records:")
        for record in store.query(limit=5):
            print(f"   - {record.id}: {record.source} ({record.collected_at})")
    else:
        print("Failed to parse result.")
else:
    print("No document to parse.")
