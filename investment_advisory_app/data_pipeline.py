import json
import requests
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime, timedelta
from requests.exceptions import RequestException
from time import sleep
from json import dumps, loads
import pandas as pd
from questdb.ingress import Sender

def fetch_symbol_data(symbol):
    try:
        api_key = "bf7cd1884b5b230fe36c6b3a643e4e34" # jWGIkWgNiFf7mJynZvy5wHNrsd3w0qZw
        base_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            'apikey': api_key,
            'serietype': 'line',
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        return data.get('historical', [])
    except RequestException as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return []
print(fetch_symbol_data("AAPL"))
def group_data_by_years(data, batch_size_years=5):
    result = []
    current_batch = []
    current_year = None

    for entry in data:
        entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
        entry_year = entry_date.year

        if current_year is None or entry_year - current_year <= batch_size_years:
            current_batch.append(entry)
        else:
            result.append(current_batch)
            current_batch = [entry]

        current_year = entry_year

    if current_batch:
        result.append(current_batch)

    return result

def send_data_to_kafka(producer, topic, symbol, data):
    try:
        producer.send(topic, value={'symbol': symbol, 'data': data})
        producer.flush()
    except Exception as e:
        print(f"Error sending data to Kafka: {str(e)}")
        

def main():
    kafka_bootstrap_servers = 'localhost:9092'
    kafka_topic = 'fmp_stock_data'
    symbols = ['AAPL', 'GOOGL', 'MSFT']  # Add more symbols as needed

    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=5,  # Number of retries for failed sends
        acks='all',  # Wait for all replicas to acknowledge
        linger_ms=100,  # Time to wait for more messages before sending a batch
        api_version=(0,11,5),
    )
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
    'fmp_stock_data',
     bootstrap_servers=['127.0.0.1:9092'],
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     group_id='my-group',
     value_deserializer=lambda x: loads(x.decode('utf-8')),
     api_version=(0,11,5),)
     

    for symbol in symbols:
        symbol_data = fetch_symbol_data(symbol)
        print("length of data", len(symbol_data))
        batches = group_data_by_years(symbol_data, batch_size_years=5)
        print('length of batches', len(batches))

        for batch in batches:
            send_data_to_kafka(producer, kafka_topic, symbol, batch)
            print("batch sent")
            sleep(0.1)  # Introduce a small delay between messages to avoid overwhelming Kafka

    producer.close()
    
    # Consume data from Kafka and insert into QuestDB
    for message in consumer:
        data = message.value
        df = pd.DataFrame(data)
        new_data = pd.json_normalize(df['data'])
        result = pd.concat([df[['symbol']], new_data], axis=1)
        df = result
        print(df.sample(20))
        with Sender('localhost', 9009) as sender:
            sender.dataframe(df, table_name='stocks_from_data_pipeline')
            sender.flush()
        

if __name__ == "__main__":
    main()
