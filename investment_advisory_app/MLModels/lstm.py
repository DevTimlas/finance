import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tqdm import tqdm
import matplotlib.pyplot as plt

def train_lstm_model(data_file, sequence_length, batch_size=32, epochs=100, learning_rate=0.001, patience=10):
    # Load the stock price data
    df = pd.read_csv(data_file)
    dataset = df['Close'].values.reshape(-1, 1)

    # Scale the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)

    # Split the data into training and testing sets
    train_size = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:]

    # Create sequences for the LSTM model
    def create_sequences(data, sequence_length):
        X = []
        y = []
        for i in range(len(data) - sequence_length):
            X.append(data[i:i+sequence_length])
            y.append(data[i+sequence_length])
        return np.array(X), np.array(y)

    X_train, y_train = create_sequences(train_data, sequence_length)
    X_test, y_test = create_sequences(test_data, sequence_length)

    # Build the LSTM model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(sequence_length, 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=40, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(units=30))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))

    # Compile the model
    model.compile(optimizer=Adam(learning_rate=learning_rate), loss='mean_squared_error')

    # Define callbacks
    early_stopping = EarlyStopping(monitor='val_loss', patience=patience, verbose=1, restore_best_weights=True)
    checkpoint = ModelCheckpoint('best_model.h5', monitor='val_loss', save_best_only=True, verbose=1)

    # Train the model
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test), callbacks=[early_stopping, checkpoint])

    # Load the best model
    model.load_weights('best_model.h5')

    # Evaluate the model
    train_loss = model.evaluate(X_train, y_train)
    test_loss = model.evaluate(X_test, y_test)

    print('Train Loss:', train_loss)
    print('Test Loss:', test_loss)

    # Make predictions
    last_sequence = train_data[-sequence_length:]
    last_sequence = last_sequence.reshape(1, sequence_length, 1)

    predicted_values = []
    for _ in tqdm(range(len(test_data)), desc="Making Prediction"):
        predicted_value = model.predict(last_sequence, verbose=0)[0]
        predicted_values.append(predicted_value)
        last_sequence = np.append(last_sequence[:, 1:, :], [[predicted_value]], axis=1)

    predicted_values = np.array(predicted_values).reshape(-1, 1)
    predicted_values = scaler.inverse_transform(predicted_values)

    # Inverse transform the original test data
    original_values = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Print the predicted stock prices
    for i in range(len(predicted_values)):
        print(f'Predicted Stock Price at Time Step {i+1}: {predicted_values[i][0]}')

    # preds = predicted_values[-(len(predicted_values) - len(original_values)):]
    # print(f"Future {sequence_length} days predictions: {preds}")
    # return preds

    # Plot the original test data and the predicted values
    plt.figure(figsize=(14, 7))
    plt.plot(original_values, label='Original Data', color='blue')
    plt.plot(predicted_values, label='Predicted Data', color='red')
    plt.title('Stock Price Prediction')
    plt.xlabel('Time')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.show()

train_lstm_model("/home/tim/jupyterNotes/fivv/investment_advisory_app/ml_data.csv", 5)
