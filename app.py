import logging
from db.fetch_data import fetch_order_data
from processing.clean_data import parse_and_clean_data
from processing.aggregate import aggregate_daily_sales
from processing.feature_engineering import build_features
from model.train_model import train_and_evaluate
from model.save_load import save_model, load_model
from model.predict import predict_next_day

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

    # 4. Train Model
    logger.info("--- Step 4: Model Training ---")
    model = train_and_evaluate(dfFeatures)
    
    if model:
        # 5. Save Model
        save_model(model)
        
        # 6. Predict
        logger.info("--- Step 5: Prediction ---")
        loaded_model = load_model()
        predictions = predict_next_day(loaded_model, dfFeatures)
        if predictions is not None and not predictions.empty:
            logger.info("Sample Predictions for Next Day:")
            logger.info(f"\n{predictions.head(10)}")
        else:
            logger.warning("Could not generate predictions.")
            
    logger.info("Pipeline Execution Completed Successfully.")

if __name__ == "__main__":
    main()
