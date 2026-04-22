import pandas as pd
import logging

logger = logging.getLogger(__name__)

def predict_next_day(model, df, product_id=None):
    """
    Predicts next day's sales for all products or a specific product
    using the latest available data, fully pipelined with tree encoders.
    """
    if model is None or df.empty:
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
    
    # Isolate strictly the synthesized target day per product
    pred_input = next_day_df.groupby("productId").tail(1).copy()
    
    # Make sure we don't drop products that simply don't have exactly 7 days history
    # For a robust random forest, filling standard lags dynamically is better, 
    # but here we require them because the tree needs dense data nodes.
    pred_input = pred_input.dropna(subset=["lag_1", "lag_7", "weekday", "avg_7"])
    
    if pred_input.empty:
        logger.warning("Not enough historical data isolated to generate structural future predictions.")
        return None
        
    # The new pipeline expects product ID explicit mapping
    X_pred = pred_input[["productId", "lag_1", "lag_7", "weekday", "avg_7", "month", "is_weekend"]]
    pred_sales = model.predict(X_pred)
    
    pred_input["predicted_sales"] = pred_sales
    pred_input["predicted_sales"] = pred_input["predicted_sales"].clip(lower=0) 
    
    results = pred_input[["productId", "date", "predicted_sales"]]
    return results
