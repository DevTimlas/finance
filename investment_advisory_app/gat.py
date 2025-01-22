import yfinance as yf
import pandas as pd
# from questdb import connect
from questdb.ingress import Sender
import numpy as np

symbol = "AAPL"
start_date = "2022-01-01"
end_date = "2024-01-01"

data = yf.download(symbol, start=start_date, end=end_date)
data = data.iloc[::-1]

# Convert DataFrame to be C-contiguous
for col in data.columns:
    data[col] = np.ascontiguousarray(data[col])

# data = pd.DataFrame(np.ascontiguousarray(data.values), columns=data.columns)

print(data)

# Assuming `historical_data` is a DataFrame with OHLCV data
# connection = connect(url="http://localhost:9000")
# connection.query_table(
#    f"CREATE TABLE ticks(symbol STRING, timestamp TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE) timestamp(timestamp) PARTITION BY DAY"
# )
# connection.insert("ticks", data.to_dict(orient='records'))
with Sender('localhost', 9009) as sender:
    sender.dataframe(data, table_name='stocks')
    sender.flush()
