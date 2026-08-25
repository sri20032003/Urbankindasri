# ML Ensemble for Signal Prediction

import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import joblib
import os

logger = logging.getLogger(__name__)


class MLPredictionOutput(BaseModel):
    """ML model prediction output."""
    direction_probability: float  # 0-1, probability of upside
    expected_return_pct: float    # Expected return %
    volatility: float             # Expected volatility %
    target_probability: float     # Probability of reaching target
    stop_probability: float       # Probability of hitting stop
    model_confidence: float       # 0-1, confidence in prediction
    model_agreement: float        # 0-1, agreement across models
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class MLEnsemble:
    """Machine Learning Ensemble for predictions."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model_path = self.config.get('model_path', 'models/ml_models/')
        
        # Initialize models
        self.xgb_model: Optional[xgb.XGBClassifier] = None
        self.lgb_model: Optional[lgb.LGBMClassifier] = None
        self.rf_model: Optional[RandomForestClassifier] = None
        self.rf_regressor: Optional[RandomForestRegressor] = None
        
        self.scaler = StandardScaler()
        self.feature_names = []
        
        logger.info("Initializing ML Ensemble")
        self._load_models()
    
    async def predict(
        self,
        features: Dict[str, float],
        feature_names: List[str]
    ) -> MLPredictionOutput:
        """Generate ML predictions.
        
        Args:
            features: Feature dictionary
            feature_names: Feature names in order
        
        Returns:
            ML prediction output
        """
        try:
            # Prepare feature vector
            X = np.array([features.get(name, 0.0) for name in feature_names]).reshape(1, -1)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Get predictions from each model
            predictions = {
                'xgb': None,
                'lgb': None,
                'rf': None
            }
            
            if self.xgb_model:
                xgb_pred = self.xgb_model.predict_proba(X_scaled)[0][1]
                predictions['xgb'] = xgb_pred
            
            if self.lgb_model:
                lgb_pred = self.lgb_model.predict_proba(X_scaled)[0][1]
                predictions['lgb'] = lgb_pred
            
            if self.rf_model:
                rf_pred = self.rf_model.predict_proba(X_scaled)[0][1]
                predictions['rf'] = rf_pred
            
            # Calculate ensemble prediction
            valid_preds = [p for p in predictions.values() if p is not None]
            
            if not valid_preds:
                # Default to neutral prediction
                return self._create_default_prediction()
            
            # Average prediction
            ensemble_pred = np.mean(valid_preds)
            agreement_score = 1.0 - (np.std(valid_preds) / 0.5)  # Normalize std
            agreement_score = max(0.0, min(1.0, agreement_score))
            
            # Expected return (from regressor if available)
            expected_return = 0.0
            if self.rf_regressor:
                expected_return = self.rf_regressor.predict(X_scaled)[0]
            else:
                # Estimate from direction probability
                expected_return = (ensemble_pred - 0.5) * 4.0  # -2% to +2%
            
            # Volatility estimate
            volatility = 2.0 + (abs(ensemble_pred - 0.5) * 2.0)  # 2%-3%
            
            # Target/Stop probabilities
            if ensemble_pred > 0.6:
                target_prob = min(0.95, ensemble_pred)
                stop_prob = max(0.05, 1.0 - ensemble_pred)
            elif ensemble_pred < 0.4:
                target_prob = max(0.05, 1.0 - ensemble_pred)
                stop_prob = min(0.95, ensemble_pred)
            else:
                target_prob = 0.50
                stop_prob = 0.50
            
            return MLPredictionOutput(
                direction_probability=float(ensemble_pred),
                expected_return_pct=float(expected_return),
                volatility=float(volatility),
                target_probability=float(target_prob),
                stop_probability=float(stop_prob),
                model_confidence=float(agreement_score),
                model_agreement=float(agreement_score),
                timestamp=datetime.now(),
                metadata={
                    'xgb_pred': float(predictions['xgb']) if predictions['xgb'] else None,
                    'lgb_pred': float(predictions['lgb']) if predictions['lgb'] else None,
                    'rf_pred': float(predictions['rf']) if predictions['rf'] else None,
                    'prediction_std': float(np.std(valid_preds)) if len(valid_preds) > 1 else 0.0,
                    'ensemble_method': 'average'
                }
            )
        
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            return self._create_default_prediction()
    
    def _load_models(self):
        """Load pre-trained models from disk."""
        try:
            os.makedirs(self.model_path, exist_ok=True)
            
            # Try to load XGBoost
            xgb_path = os.path.join(self.model_path, 'xgb_model.joblib')
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                logger.info("Loaded XGBoost model")
            
            # Try to load LightGBM
            lgb_path = os.path.join(self.model_path, 'lgb_model.joblib')
            if os.path.exists(lgb_path):
                self.lgb_model = joblib.load(lgb_path)
                logger.info("Loaded LightGBM model")
            
            # Try to load Random Forest
            rf_path = os.path.join(self.model_path, 'rf_model.joblib')
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
                logger.info("Loaded Random Forest model")
            
            # Load regressor
            reg_path = os.path.join(self.model_path, 'rf_regressor.joblib')
            if os.path.exists(reg_path):
                self.rf_regressor = joblib.load(reg_path)
                logger.info("Loaded Random Forest Regressor")
        
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {str(e)}")
    
    def save_models(self):
        """Save trained models to disk."""
        try:
            os.makedirs(self.model_path, exist_ok=True)
            
            if self.xgb_model:
                joblib.dump(self.xgb_model, os.path.join(self.model_path, 'xgb_model.joblib'))
            
            if self.lgb_model:
                joblib.dump(self.lgb_model, os.path.join(self.model_path, 'lgb_model.joblib'))
            
            if self.rf_model:
                joblib.dump(self.rf_model, os.path.join(self.model_path, 'rf_model.joblib'))
            
            if self.rf_regressor:
                joblib.dump(self.rf_regressor, os.path.join(self.model_path, 'rf_regressor.joblib'))
            
            logger.info("Saved all models")
        
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    def _create_default_prediction(self) -> MLPredictionOutput:
        """Create default neutral prediction."""
        return MLPredictionOutput(
            direction_probability=0.5,
            expected_return_pct=0.0,
            volatility=2.0,
            target_probability=0.5,
            stop_probability=0.5,
            model_confidence=0.3,
            model_agreement=0.3,
            timestamp=datetime.now()
        )
