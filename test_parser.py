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
        print(f"2nd Prize: {result.second_prize} ({result.second_prize_location})")
        print(f"3rd Prize: {result.third_prize} ({result.third_prize_location})")
        print(f"Consolation Prizes: {len(result.consolation_prizes)} found")
        print(f"4th Prize Numbers: {len(result.fourth_prize_numbers)} found")
        print(f"5th Prize Numbers: {len(result.fifth_prize_numbers)} found")
        print(f"6th Prize Numbers: {len(result.sixth_prize_numbers)} found")
        print(f"7th Prize Numbers: {len(result.seventh_prize_numbers)} found")
        print(f"8th Prize Numbers: {len(result.eighth_prize_numbers)} found")
        print(f"9th Prize Numbers: {len(result.ninth_prize_numbers)} found")
    else:
        print("Failed to parse result.")
else:
    print("No document to parse.")
