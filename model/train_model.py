from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    logger.info(f"Model Evaluation - Mean Absolute Error (MAE): {mae:.4f}")
    return mae

def train_and_evaluate(df):
    """
    Performs time-based split, trains a RandomForestRegressor pipeline isolating text features,
    and returns the evaluated model.
    """
    if df.empty:
        logger.error("Empty dataframe provided for training.")
        return None

    features = ["productId", "lag_1", "lag_7", "weekday", "avg_7", "month", "is_weekend"]
    target = "sales"

    # Time-based split: Train on earlier data, test on the latest 20%
    dates = df["date"].sort_values().unique()
    split_index = int(len(dates) * 0.8)
    split_date = dates[split_index]
    
    logger.info(f"Splitting data. Train < {split_date}, Test >= {split_date}")
    
    train_df = df[df["date"] < split_date]
    test_df = df[df["date"] >= split_date]
    
    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]
    
    logger.info(f"Training set shape: {X_train.shape}")
    logger.info(f"Testing set shape: {X_test.shape}")
    
    # Preprocessor automatically converts productId dynamically leaving numeric variables standard
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), ["productId"])
        ],
        remainder="passthrough"
    )

    # Wrap inside tree-estimator
    model_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=50, 
            min_samples_leaf=3,
            max_depth=15,
            n_jobs=-1,
            random_state=42
        ))
    ])
    
    logger.info("Training Model...")
    model_pipeline.fit(X_train, y_train)
    
    # Evaluate
    logger.info("Evaluating predictions on Hold-out testing set...")
    y_pred = model_pipeline.predict(X_test)
    evaluate_model(y_test, y_pred)
    
    return model_pipeline
