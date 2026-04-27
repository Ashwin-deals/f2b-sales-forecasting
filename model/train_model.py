from xgboost import XGBRegressor
import logging

logger = logging.getLogger(__name__)

def train_xgboost(X_train, y_train):
    """
    Trains an XGBoost regression model on the provided data.
    """
    if X_train.empty or y_train.empty:
        logger.error("Empty dataframe provided for training XGBoost.")
        return None

    model = XGBRegressor(
        objective="reg:tweedie",
        tweedie_variance_power=1.3,
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    logger.info("Training Regression Model (XGBoost Tweedie) on Full Data...")
    model.fit(X_train, y_train)
    
    return model

