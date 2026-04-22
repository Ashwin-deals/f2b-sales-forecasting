import joblib
import os
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = "model.pkl"

def save_model(model):
    """
    Saves the trained model to the local filesystem.
    """
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Model successfully saved to {MODEL_PATH}")

def load_model():
    """
    Loads the trained model from the local filesystem.
    """
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        logger.info(f"Model successfully loaded from {MODEL_PATH}")
        return model
    else:
        logger.error(f"Model file {MODEL_PATH} not found.")
        return None
