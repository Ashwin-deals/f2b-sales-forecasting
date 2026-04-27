from sklearn.ensemble import RandomForestClassifier
import logging

logger = logging.getLogger(__name__)

def train_classifier(X_train, y_train):
    """
    Trains a RandomForestClassifier to predict if demand exists (will_sell).
    """
    logger.info("Training Classification Model (Random Forest)...")
    
    model = RandomForestClassifier(
        n_estimators=100, 
        random_state=42, 
        class_weight="balanced", 
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    return model
