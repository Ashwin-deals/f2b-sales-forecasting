import numpy as np
import pandas as pd
import logging
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

# Suppress TF logging
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

logger = logging.getLogger(__name__)

def create_sequences(data, window_size=7):
    """
    Convert a 1D array into overlapping sequences
    """
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:(i + window_size)])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)

def train_and_evaluate_lstm(df, top_n=2):
    """
    Trains a simple LSTM model on the top N active products to predict next day sales.
    Uses a 7-day window.
    """
    if df.empty:
        logger.error("Empty dataframe provided for LSTM training.")
        return
        
    logger.info(f"--- Starting LSTM Training on Top {top_n} Products ---")
    
    # 1. Find the most active products based on total sales
    top_products = df.groupby("productId")["sales"].sum().nlargest(top_n).index
    logger.info(f"Selected products for LSTM: {list(top_products)}")
    
    for product_id in top_products:
        logger.info(f"\nTraining LSTM for Product: {product_id}")
        
        # 2. Extract product data, sorted chronologically
        prod_df = df[df["productId"] == product_id].sort_values("date")
        sales_data = prod_df["sales"].values.reshape(-1, 1)
        
        if len(sales_data) < 14:
            logger.warning(f"Not enough data for product {product_id} to train LSTM. Skipping.")
            continue
            
        # 3. Normalize data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_sales = scaler.fit_transform(sales_data)
        
        # 4. Prepare sequences
        window_size = 7
        X, y = create_sequences(scaled_sales, window_size)
        
        # Split into train/test (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # LSTM expects 3D input: (samples, time_steps, features)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        logger.info(f"Window size: {window_size}")
        logger.info(f"X shape: {np.reshape(X, (X.shape[0], X.shape[1], 1)).shape}")
        logger.info(f"y shape: {y.shape}")
        logger.info(f"Sample sequence (X[0]):\n{X[0]}")
        
        model_path = f"lstm_model_{product_id}.keras"
        if os.path.exists(model_path):
            logger.info(f"Loading existing LSTM model for {product_id}...")
            from tensorflow.keras.models import load_model
            model = load_model(model_path)
        else:
            # 5. Build model
            model = Sequential([
                LSTM(32, activation='relu', input_shape=(window_size, 1)),
                Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mse')
            
            # 6. Train model
            logger.info("Training LSTM model...")
            model.fit(X_train, y_train, epochs=10, batch_size=16, verbose=0)
            
            # Save model
            model.save(model_path)
        
        # 7. Predict and Evaluate
        logger.info("Evaluating LSTM...")
        y_pred_scaled = model.predict(X_test, verbose=0)
        
        # Inverse transform
        y_pred = scaler.inverse_transform(y_pred_scaled)
        y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))
        
        mae = mean_absolute_error(y_test_actual, y_pred)
        logger.info(f"LSTM MAE for {product_id}: {mae:.4f}")
        
        # Evaluate non-zero actuals
        y_test_flat = y_test_actual.flatten()
        y_pred_flat = y_pred.flatten()
        mask = y_test_flat > 0
        if mask.sum() > 0:
            mae_non_zero = mean_absolute_error(y_test_flat[mask], y_pred_flat[mask])
            logger.info(f"LSTM MAE (Non-zero actuals only) for {product_id}: {mae_non_zero:.4f}")
            
        # Sample predictions
        comp_df = pd.DataFrame({
            "Actual": y_test_flat,
            "LSTM_Predicted": y_pred_flat
        })
        logger.info(f"LSTM Sample Predictions for {product_id}:")
        non_zero_sample = comp_df[comp_df["Actual"] > 0].head(3)
        zero_sample = comp_df[comp_df["Actual"] == 0].head(3)
        logger.info(f"\n{pd.concat([non_zero_sample, zero_sample])}")
