from collector.connectors.keralam_lottery import KeralamLotteryConnector

connector = KeralamLotteryConnector()

# Get the latest serial
serial = connector.get_latest_serial()
print(f"Latest Serial: {serial}")

# Fetch the latest result
doc = connector.fetch_latest()
print(f"Document ID: {doc.id}")
print(f"Status Code: {doc.status_code}")
print(f"Content Length: {len(doc.content) if doc.content else 0}")
