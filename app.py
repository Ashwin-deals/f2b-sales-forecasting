import logging
from db.fetch_data import fetch_order_data
from processing.clean_data import parse_and_clean_data
from processing.aggregate import aggregate_daily_sales
from processing.feature_engineering import build_features
from model.train_model import train_xgboost
from model.save_load import save_model, load_model
from model.predict import predict_next_day

USE_LSTM = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

import joblib
import os

MODEL_PATH = "model.pkl"

def get_or_train_model(X_train, y_train):
    if os.path.exists(MODEL_PATH):
        try:
            logger.info("Loading existing model...")
            model = joblib.load(MODEL_PATH)
            model.predict(X_train.head(1))
            return model
        except Exception as e:
            logger.warning(f"Stale/incompatible model.pkl detected ({e}). Retraining from scratch...")
            os.remove(MODEL_PATH)
    
    logger.info("Training new model...")
    model = train_xgboost(X_train, y_train)
    joblib.dump(model, MODEL_PATH)
    return model

def check_drift(df):
    recent = df.sort_values("date").tail(7)
    recent_mean = recent["sales"].mean()
    historical_mean = df["sales"].mean()
    drift = abs(recent_mean - historical_mean)
    logger.info(f"Recent Mean: {recent_mean:.2f}, Historical Mean: {historical_mean:.2f}")
    if drift > 2:
        logger.warning("⚠️ WARNING: Data drift detected!")

def main():
    logger.info("Starting Demand Forecasting Pipeline...")

    # 1. Fetch
    logger.info("--- Step 1: Fetching Data ---")
    orderdetails, retailorders = fetch_order_data()

    # 2. Process
    logger.info("--- Step 2: Processing Data ---")
    dfRaw = parse_and_clean_data(orderdetails, retailorders)
    logger.info(f"Combined Raw DataFrame shape: {dfRaw.shape}")
    
    dfAgg = aggregate_daily_sales(dfRaw)
    logger.info(f"Aggregated DataFrame shape: {dfAgg.shape}")

    # 3. Feature Engineering
    logger.info("--- Step 3: Feature Engineering ---")
    dfFeatures = build_features(dfAgg)
    logger.info(f"Feature-engineered DataFrame shape: {dfFeatures.shape}")

    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    MODE = "backtest" # or "live"
    RUN_BACKTEST_WINDOW = True
    BACKTEST_DAYS = 7  # rolling validation window
    
    if not dfFeatures.empty:
        max_date = dfFeatures["date"].max()
        
        if MODE == "backtest" and RUN_BACKTEST_WINDOW:
            loop_days = range(BACKTEST_DAYS + 1, 1, -1)
        else:
            loop_days = [0]
            
        backtest_results = []
        
        for i in loop_days:
            if MODE == "backtest":
                cutoff_date = max_date - pd.Timedelta(days=i)
            else:
                cutoff_date = max_date
                
            prediction_date = cutoff_date + pd.Timedelta(days=1)
            
            logger.info(f"--- Pipeline Run for Prediction Date: {prediction_date.date() if hasattr(prediction_date, 'date') else prediction_date} ---")
            
            df_train = dfFeatures[dfFeatures["date"] <= cutoff_date].copy()
            
            # 4. Train Models
            features = [
                "lag_1", "lag_7", "avg_7", "avg_30", "std_7",
                "weekday", "is_weekend", "days_since_sale"
            ]
            
            X_train_reg = df_train[features]
            y_reg = df_train["sales"]
            
            check_drift(df_train)
            reg_model = get_or_train_model(X_train_reg, y_reg)
            
            if reg_model:
                # 5. Predict Next Day
                best_preds = predict_next_day(reg_model, df_train)
                
                if best_preds is not None and not best_preds.empty:
                    # Demand Classification
                    def classify_demand(pred):
                        if pred == 0:
                            return "NO DEMAND"
                        elif pred < 2:
                            return "LOW"
                        elif pred < 5:
                            return "NORMAL"
                        else:
                            return "HIGH"
                            
                    best_preds["demand_level"] = best_preds["predicted_sales"].apply(classify_demand)
                    
                    run_date = datetime.now().strftime("%Y-%m-%d")
                    date_str = prediction_date.strftime("%Y-%m-%d") if hasattr(prediction_date, "strftime") else str(prediction_date)
                    
                    # --- Structured forecast record for forecast_history.csv ---
                    forecast_record = best_preds[["productId", "date", "predicted_sales", "demand_level"]].copy()
                    forecast_record.rename(columns={"date": "target_date"}, inplace=True)
                    forecast_record.insert(0, "run_date", run_date)
                    
                    FORECAST_HISTORY_PATH = "forecast_history.csv"
                    history_exists = os.path.exists(FORECAST_HISTORY_PATH)
                    temp_history = "temp_forecast_history.csv"
                    
                    if history_exists:
                        existing = pd.read_csv(FORECAST_HISTORY_PATH, low_memory=False)
                        existing = existing[~(
                            (existing["run_date"] == run_date) &
                            (existing["target_date"].isin(forecast_record["target_date"].astype(str)))
                        )]
                        combined = pd.concat([existing, forecast_record], ignore_index=True)
                    else:
                        combined = forecast_record
                    
                    combined.to_csv(temp_history, index=False)
                    os.replace(temp_history, FORECAST_HISTORY_PATH)
                    
                    # --- Output Columns for demand_report.csv ---
                    demand_report = best_preds[["productId", "date", "predicted_sales", "demand_level"]]
                    demand_report.to_csv("demand_report.csv", index=False)
                    
                    # --- Console Summary ---
                    print("\n--- DEMAND INTELLIGENCE SUMMARY ---")
                    print(f"Prediction Date:    {date_str}")
                    print(f"Active Products:    {len(best_preds)}")
                    print(f"Total Next-Day Demand: {best_preds['predicted_sales'].sum():.2f}")
                    print(f"  HIGH:             {(best_preds['demand_level'] == 'HIGH').sum()}")
                    print(f"  NORMAL:           {(best_preds['demand_level'] == 'NORMAL').sum()}")
                    print(f"  LOW:              {(best_preds['demand_level'] == 'LOW').sum()}")
                    print(f"  NO DEMAND:        {(best_preds['demand_level'] == 'NO DEMAND').sum()}")
                    
                    pred_std = best_preds["predicted_sales"].std()
                    pred_round = best_preds["predicted_sales"].round(2)
                    pct_identical = (pred_round.value_counts().max() / len(pred_round) * 100) if len(pred_round) > 0 else 0
                    print(f"\n--- PREDICTION DISTRIBUTION ---")
                    print(f"Prediction Std Dev:      {pred_std:.4f}")
                    print(f"% Identical Predictions: {pct_identical:.1f}%")
                    print(f"Min Forecast:            {best_preds['predicted_sales'].min():.4f}")
                    print(f"Max Forecast:            {best_preds['predicted_sales'].max():.4f}")
                    
                    logger.info(f"Appended {len(forecast_record)} rows to forecast_history.csv")
                    logger.info("Demand Intelligence Report Generated Successfully")
                
                # 7. Backtest Evaluation
                if MODE == "backtest" and best_preds is not None and not best_preds.empty:
                    df_actual = dfFeatures[dfFeatures["date"] == prediction_date]
                    
                    actual_1 = df_actual.set_index("productId")["sales"]
                    pred_1 = best_preds.set_index("productId")["predicted_sales"]
                    
                    actual_aligned, pred_aligned = actual_1.align(pred_1, join='inner')
                    actual_aligned = actual_aligned.fillna(0)
                    
                    if not actual_aligned.empty:
                        df_eval = pd.DataFrame({
                            "sales": actual_aligned,
                            "predicted_sales": pred_aligned
                        }).reset_index()
                        df_eval["prediction_date"] = date_str
                        df_eval["error"] = abs(df_eval["predicted_sales"] - df_eval["sales"])
                        
                        df_eval["pred_zero"] = df_eval["predicted_sales"] == 0
                        df_eval["actual_zero"] = df_eval["sales"] == 0
                        zero_accuracy = (df_eval["pred_zero"] == df_eval["actual_zero"]).mean()
                        
                        mae = df_eval["error"].mean()
                        mask_nz = df_eval["sales"] > 0
                        mae_nz = df_eval.loc[mask_nz, "error"].mean() if mask_nz.sum() > 0 else 0.0
                        
                        top_errors = df_eval.sort_values("error", ascending=False).head(5)
                        best = df_eval.sort_values("error").head(5)
                        
                        print(f"\nZero Demand Accuracy: {zero_accuracy:.0%}")
                        print("\n--- TOP ERRORS ---")
                        for _, row in top_errors.iterrows():
                            print(f"({row['productId']}, predicted: {row['predicted_sales']:.2f}, actual: {row['sales']:.2f}, error: {row['error']:.2f})")
                        print("\n--- BEST PREDICTIONS ---")
                        for _, row in best.iterrows():
                            print(f"({row['productId']}, predicted: {row['predicted_sales']:.2f}, actual: {row['sales']:.2f}, error: {row['error']:.2f})")
                        
                        print(f"\nMAE: {mae:.4f}  |  Non-zero Actuals MAE: {mae_nz:.4f}")
                        
                        backtest_results.append({
                            "Date": date_str,
                            "MAE": mae,
                            "Non-zero MAE": mae_nz
                        })
                        
                        logger.info("----- VALIDATION SUMMARY -----")
                        logger.info(f"Total Products Evaluated: {len(df_eval)}")
                        logger.info(f"MAE:           {mae:.4f}")
                        logger.info(f"Non-zero MAE:  {mae_nz:.4f}")
                    else:
                        logger.warning("No actual sales data found for prediction date window to compare against.")
            else:
                logger.warning("Model could not be trained.")
                
        if MODE == "backtest" and backtest_results and RUN_BACKTEST_WINDOW:
            print("\nRolling Backtest Performance:")
            print(f"{'Date':<12} {'MAE':<10} {'Non-zero MAE':<14}")
            print("-" * 38)
            for res in backtest_results:
                print(f"{res['Date']:<12} {res['MAE']:<10.4f} {res['Non-zero MAE']:<14.4f}")

    else:
        logger.warning("No features extracted.")
        
    logger.info("Pipeline Execution Completed Successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Pipeline failed: {e}")
