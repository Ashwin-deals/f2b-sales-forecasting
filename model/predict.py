import pandas as pd
import logging

logger = logging.getLogger(__name__)

def predict_next_day(reg_model, df, product_id=None):
    """
    Predicts next day's sales using a single-stage XGBoost regression model.
    """
    if reg_model is None or df.empty:
        return None
        
    if product_id:
        df = df[df["productId"] == product_id]
        if df.empty:
            logger.warning(f"No data available for product {product_id}")
            return None
            
    df = df.sort_values(["productId", "date"])
    
    # Generate the dummy rows to synthesize exactly 1 day into the future correctly
    recent_data = df.groupby("productId").tail(8).copy()
    dummy_rows = []
    
    for pid in recent_data["productId"].unique():
        p_data = recent_data[recent_data["productId"] == pid]
        last_date = p_data["date"].max()
        next_date = last_date + pd.Timedelta(days=1)
        # Placeholder struct
        dummy = {"productId": pid, "date": next_date, "sales": 0}
        dummy_rows.append(dummy)
        
    next_day_df = pd.concat([recent_data, pd.DataFrame(dummy_rows)], ignore_index=True)
    next_day_df = next_day_df.sort_values(["productId", "date"])
    
    # Engineer synthetic properties over the tail subset
    next_day_df["weekday"] = next_day_df["date"].dt.dayofweek
    next_day_df["month"] = next_day_df["date"].dt.month
    next_day_df["is_weekend"] = next_day_df["weekday"].apply(lambda x: 1 if x >= 5 else 0)
    
    next_day_df["lag_1"] = next_day_df.groupby("productId")["sales"].shift(1)
    next_day_df["lag_7"] = next_day_df.groupby("productId")["sales"].shift(7)
    next_day_df["avg_7"] = next_day_df.groupby("productId")["sales"].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
    )
    
    # Advanced Classification Features
    next_day_df["avg_3"] = next_day_df.groupby("productId")["sales"].transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
    next_day_df["trend"] = next_day_df["avg_3"] - next_day_df["avg_7"]
    
    next_day_df["last_sale_date"] = next_day_df.apply(lambda row: row["date"] if row["sales"] > 0 else pd.NaT, axis=1)
    next_day_df["last_sale_date"] = next_day_df.groupby("productId")["last_sale_date"].transform(lambda x: x.shift(1).ffill())
    next_day_df["days_since_sale"] = (next_day_df["date"] - next_day_df["last_sale_date"]).dt.days
    next_day_df["days_since_sale"] = next_day_df["days_since_sale"].fillna(0)
    next_day_df.drop(columns=["last_sale_date"], inplace=True)
    
    next_day_df["std_7"] = next_day_df.groupby("productId")["sales"].transform(lambda x: x.shift(1).rolling(window=7, min_periods=1).std()).fillna(0)
    
    from processing.holidays import HOLIDAYS
    next_day_df["is_holiday"] = next_day_df["date"].astype(str).isin(HOLIDAYS).astype(int)
    next_day_df["is_pre_holiday"] = (next_day_df["date"] + pd.Timedelta(days=1)).astype(str).isin(HOLIDAYS).astype(int)
    
    # Isolate strictly the synthesized target day per product
    pred_input = next_day_df.groupby("productId").tail(1).copy()
    
    pred_input = pred_input.dropna(subset=["lag_1", "lag_7", "weekday", "avg_7"])
    
    if pred_input.empty:
        logger.warning("Not enough historical data isolated to generate structural future predictions.")
        return None
        
    # The new pipeline uses ONLY numeric features, NO productId
    features = [
        "lag_1", "lag_7", "avg_7", "avg_3", "trend", 
        "days_since_sale", "std_7",
        "weekday", "month", "is_weekend",
        "is_holiday", "is_pre_holiday"
    ]
    X_pred = pred_input[features]
    
    # Regression prediction
    pred_input["predicted_sales"] = reg_model.predict(X_pred)
    
    # Baseline post-processing
    pred_input["predicted_sales"] = pred_input["predicted_sales"].clip(lower=0) 
    
    results = pred_input[["productId", "date", "predicted_sales", "avg_7"]]
    return results
