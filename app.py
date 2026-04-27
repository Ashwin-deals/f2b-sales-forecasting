import logging
from db.fetch_data import fetch_order_data
from processing.clean_data import parse_and_clean_data
from processing.aggregate import aggregate_daily_sales
from processing.feature_engineering import build_features
from model.train_model import train_xgboost
from model.save_load import save_model, load_model
from model.predict import predict_next_day
from model.train_lstm import train_and_evaluate_lstm

USE_LSTM = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
    if not dfFeatures.empty:
        logger.info(f"Sample features:\n{dfFeatures.head(3)}")

    import os
    import pandas as pd
    import numpy as np
    from datetime import datetime
    from sklearn.metrics import mean_absolute_error
    
    MODE = "backtest" # or "live"
    
    if not dfFeatures.empty:
        max_date = dfFeatures["date"].max()
        
        loop_days = range(6, 1, -1) if MODE == "backtest" else [0]
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
                "lag_1", "lag_7", "avg_7", "avg_3", "trend", 
                "days_since_sale", "std_7",
                "weekday", "month", "is_weekend",
                "is_holiday", "is_pre_holiday"
            ]
            
            # Stage 2: Regression Training (Tweedie on ALL Data)
            X_train_reg = df_train[features]
            y_reg = df_train["sales"]
            
            reg_model = train_xgboost(X_train_reg, y_reg)
            
            if reg_model:
                # 5. Predict
                best_preds = predict_next_day(reg_model, df_train)
                
                if best_preds is not None and not best_preds.empty:
                    # Post-processing: Adaptive threshold and dynamic cap
                    best_preds["predicted_sales"] = best_preds["predicted_sales"].clip(lower=0)
                    
                    def clean_prediction(row):
                        if row["avg_7"] == 0:
                            return 0 if row["predicted_sales"] < 0.8 else row["predicted_sales"]
                        else:
                            return 0 if row["predicted_sales"] < 0.4 else row["predicted_sales"]
                            
                    best_preds["predicted_sales"] = best_preds.apply(clean_prediction, axis=1)
                    
                    best_preds["predicted_sales"] = best_preds.apply(
                        lambda row: min(row["predicted_sales"], max(3, row["avg_7"] * 3)),
                        axis=1
                    )
                
                # 6. Backtest Evaluation
                if MODE == "backtest":
                    df_actual = dfFeatures[dfFeatures["date"] == prediction_date]
                    
                    comparison = best_preds.merge(df_actual[["productId", "sales"]], on="productId", how="left")
                    comparison = comparison.dropna(subset=["sales"])
                    
                    if not comparison.empty:
                        mae = mean_absolute_error(comparison["sales"], comparison["predicted_sales"])
                        
                        date_str = prediction_date.strftime("%Y-%m-%d")
                        backtest_results.append({
                            "Date": date_str,
                            "MAE": mae
                        })
                        
                        if i == 2:  # Detailed logs only for the final backtest day
                            mask_nz = comparison["sales"] > 0
                            mae_nz = mean_absolute_error(comparison.loc[mask_nz, "sales"], comparison.loc[mask_nz, "predicted_sales"]) if mask_nz.sum() > 0 else float('inf')
                            comparison["error"] = abs(comparison["sales"] - comparison["predicted_sales"])
                            
                            logger.info("----- VALIDATION SUMMARY -----")
                            logger.info(f"Total Products Evaluated: {len(comparison)}")
                            logger.info(f"MAE: {mae:.4f}")
                            logger.info(f"Non-zero MAE: {mae_nz:.4f}")
                    else:
                        logger.warning("No actual sales data found for prediction date to compare against.")
                
                # 7. Convert Predictions to Business Output
                if MODE == "live" or i == 2:
                    best_preds = best_preds.fillna(0)
                    
                    def categorize(x):
                        if x == 0: return "NO DEMAND"
                        elif x < 2: return "LOW"
                        elif x < 5: return "MEDIUM"
                        else: return "HIGH"
                            
                    best_preds["demand_level"] = best_preds["predicted_sales"].apply(categorize)
                    top_products = best_preds.sort_values(by="predicted_sales", ascending=False).head(10)
                    
                    date_str = prediction_date.strftime("%Y-%m-%d")
                    best_preds.to_csv(f"daily_predictions_{date_str}.csv", index=False)
                    top_products.to_csv(f"top_products_{date_str}.csv", index=False)
                    
                    logger.info("Final Predictions Generated Successfully")
                    logger.info(f"Total Predicted Demand: {best_preds['predicted_sales'].sum():.2f}")
                    logger.info(f"Saved daily_predictions_{date_str}.csv and top_products_{date_str}.csv.")
                    
            else:
                logger.warning("Models could not be trained.")
                
        if MODE == "backtest" and backtest_results:
            print("\nDay-wise performance:")
            print(f"{'Date':<12} {'MAE':<8}")
            print("-" * 22)
            for res in backtest_results:
                print(f"{res['Date']:<12} {res['MAE']:<8.4f}")
                
    else:
        logger.warning("No features extracted.")
            
    # 7. LSTM Prototype (Disabled for production stability)
    if USE_LSTM:
        logger.info("--- Step 6: Deep Learning (LSTM) Integration ---")
        train_and_evaluate_lstm(dfFeatures, top_n=2)
            
    logger.info("Pipeline Execution Completed Successfully.")

if __name__ == "__main__":
    main()
