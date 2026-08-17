from collector.connectors.keralam_lottery import KeralamLotteryConnector
from collector.parsers.keralam_result import KeralamResultParser

connector = KeralamLotteryConnector()
parser = KeralamResultParser()

# Use a known working serial
SERIAL = 75352

# Fetch the result
doc = connector.fetch_draw(SERIAL)

if doc and doc.content:
    result = parser.parse(doc.content)

    if result:
        print(f"Lottery: {result.lottery_name}")
        print(f"Date: {result.draw_date}")
        print(f"1st Prize: {result.first_prize} ({result.first_prize_location})")
    else:
        print("Failed to parse result.")
else:
    print("No document to parse.")
