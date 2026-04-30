import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

EDGE_CASE_REPORT_PATH = "edge_case_report.csv"

def _load_edge_cases():
    phantom, missed = {}, {}
    if not os.path.exists(EDGE_CASE_REPORT_PATH):
        return phantom, missed
    try:
        ecdf = pd.read_csv(EDGE_CASE_REPORT_PATH)
        for _, row in ecdf.iterrows():
            pid, issue, days = row["productId"], row["issue"], int(row["days_affected"])
            if issue == "phantom_demand":
                phantom[pid] = max(phantom.get(pid, 0), days)
    except Exception as e:
        logger.warning(f"Could not load edge_case_report.csv: {e}")
    return phantom, missed

def predict_next_day(model, df, product_id=None):
    """
    Predicts next day's sales using a single-stage XGBoost regression model.
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
    next_day_df["is_weekend"] = next_day_df["weekday"].apply(lambda x: 1 if x >= 5 else 0)
    
    next_day_df["lag_1"] = next_day_df.groupby("productId")["sales"].shift(1)
    next_day_df["lag_7"] = next_day_df.groupby("productId")["sales"].shift(7)
    next_day_df["avg_7"] = next_day_df.groupby("productId")["sales"].transform(
        lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
    )
    
    next_day_df["last_sale_date"] = next_day_df.apply(lambda row: row["date"] if row["sales"] > 0 else pd.NaT, axis=1)
    next_day_df["last_sale_date"] = next_day_df.groupby("productId")["last_sale_date"].transform(lambda x: x.shift(1).ffill())
    next_day_df["days_since_sale"] = (next_day_df["date"] - next_day_df["last_sale_date"]).dt.days
    next_day_df["days_since_sale"] = next_day_df["days_since_sale"].fillna(0)
    next_day_df.drop(columns=["last_sale_date"], inplace=True)
    
    next_day_df["std_7"] = next_day_df.groupby("productId")["sales"].transform(lambda x: x.shift(1).rolling(window=7, min_periods=1).std()).fillna(0)
    next_day_df["avg_30"] = next_day_df.groupby("productId")["sales"].transform(lambda x: x.shift(1).rolling(window=30, min_periods=1).mean()).fillna(0)
    
    # Isolate strictly the synthesized target day per product
    pred_input = next_day_df.groupby("productId").tail(1).copy()
    
    pred_input = pred_input.dropna(subset=["lag_1", "lag_7", "weekday", "avg_7"])
    
    if pred_input.empty:
        logger.warning("Not enough historical data isolated to generate structural future predictions.")
        return None
        
    features = [
        "lag_1", "lag_7", "avg_7", "avg_30", "std_7",
        "weekday", "is_weekend", "days_since_sale"
    ]
    X_pred = pred_input[features]
    
    # Predict
    raw_preds = model.predict(X_pred)
    
    final_preds = []
    
    avg_7_arr = pred_input["avg_7"].values
    avg_30_arr = pred_input["avg_30"].values
    dss_arr = pred_input["days_since_sale"].values
    lag_1_arr = pred_input["lag_1"].values
    pids = pred_input["productId"].values
    
    phantom_days, _ = _load_edge_cases()
    
    for i, pred in enumerate(raw_preds):
        a7 = avg_7_arr[i]
        a30 = avg_30_arr[i]
        dss = dss_arr[i]
        l1 = lag_1_arr[i]
        pid = pids[i]
        
        # 1. RELAX ZERO RULE (CRITICAL)
        if a7 == 0 and l1 == 0 and pred < 0.2:
            pred = 0.0
            
        # 2. REDUCE NOISE CLIPPING
        if pred < 0.08:
            pred = 0.0
            
        # 3. REDUCE SMOOTHING
        pred = 0.9 * pred + 0.1 * a7
        
        # 4. LOOSEN CAP
        pred = min(pred, max(4.0, a30 * 3.0))
        
        # 5. ADD MINIMUM SIGNAL FLOOR (NEW)
        if pred > 0 and pred < 0.2:
            pred = 0.2
            
        # 6. ADD MOMENTUM BOOST
        if l1 > 1 or a7 > 1:
            pred *= 1.3
            
        # Persistent Phantom Demand Suppression (Optional Guard)
        if phantom_days.get(pid, 0) >= 3:
            pred = pred * 0.2
            
        # Final rounding and floor
        pred = round(pred, 2)
        pred = max(0.0, pred)
        
        final_preds.append(pred)
            
    pred_input["predicted_sales"] = final_preds 
    
    results = pred_input[[
        "productId", "date", "predicted_sales",
        "avg_7", "avg_30"
    ]]
    return results
