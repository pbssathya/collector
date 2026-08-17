from collector.connectors.keralam_lottery import KeralamLotteryConnector
from collector.parsers.keralam_result import KeralamResultParser

connector = KeralamLotteryConnector()
parser = KeralamResultParser()

# Fetch the latest result
doc = connector.fetch_latest()

if doc and doc.content:
    # The content is already bytes (PDF)
    # Pass it directly to the parser
    result = parser.parse(doc.content)

    if result:
        print(f"Lottery: {result.lottery_name}")
        print(f"Date: {result.draw_date}")
        print(f"1st Prize: {result.first_prize} ({result.first_prize_location})")
    else:
        print("Failed to parse result.")
else:
    print("No document to parse.")
