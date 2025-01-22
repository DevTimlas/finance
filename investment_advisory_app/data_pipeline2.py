from kafka import KafkaConsumer
from kafka import KafkaProducer
from json import dumps, loads
import pandas as pd
import requests
import time

symbols = ['AAPL', 'GOOGL', 'MSFT']  # Add more symbols as needed

# Initialize Kafka producer
producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],
                         value_serializer=lambda x: dumps(x).encode('utf-8'), api_version=(0,11,5),)

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'fmp_from_data2',
     bootstrap_servers=['127.0.0.1:9092'],
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     group_id='my-group',
     value_deserializer=lambda x: loads(x.decode('utf-8')),
     api_version=(0,11,5),)

# Fetch data from FMP for all symbols for past 30 years
for symbol in symbols:
    for year in range(30):
        data = requests.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={year}-01-01&to={year+1}-01-01&apikey=jWGIkWgNiFf7mJynZvy5wHNrsd3w0qZw")
        data = data.json()

        # Group data in batches of 5 years
        if year % 5 == 0:
            # Send data to Kafka topic
            producer.send('fmp_from_data2', value=data)
            # print('Record: {}'.format(data))
            time.sleep(1)  # To simulate data streaming

# Consume data from Kafka and insert into QuestDB
for message in consumer:
    data = message.value
    df = pd.DataFrame(data)
    print(df.head(20))
    df.to_csv('data.csv', index=False)

    # Insert data into QuestDB
    # requests.post('http://localhost:9000/exec', data="COPY symbols FROM 'data.csv'")

