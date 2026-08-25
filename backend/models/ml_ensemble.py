"""
ML Ensemble for direction and magnitude prediction.
Combines XGBoost, LightGBM, LSTM, and Random Forest models.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from logger_config import get_logger

logger = get_logger(__name__)

@dataclass
class MLPrediction:
    """ML ensemble prediction output."""
    timestamp: str
    stock_symbol: str
    
    # Direction prediction
    direction_probability: float  # 0-1, probability of up move
    predicted_direction: str  # 'up', 'down', 'neutral'
    
    # Magnitude predictions
    expected_return_pct: float
    p_5pct: float
    p_8pct: float
    p_12pct: float
    p_15pct: float
    p_20pct: float
    
    # Risk metrics
    expected_downside_pct: float
    prediction_confidence: float  # 0-1
    model_agreement: float  # How much do the models agree? 0-1
    
    # Detailed model outputs
    xgboost_direction: float  # 0-1
    lgb_direction: float
    lstm_direction: float
    rf_direction: float

class MLEnsemble:
    """Machine learning ensemble for stock prediction."""
    
    def __init__(self):
        self.models_loaded = False
        self.model_weights = {
            'xgboost': 0.35,
            'lgb': 0.25,
            'lstm': 0.25,
            'rf': 0.15
        }
    
    def predict(self, stock_features: pd.DataFrame, stock_symbol: str) -> MLPrediction:
        """
        Generate ML ensemble prediction.
        
        Args:
            stock_features: DataFrame with computed features
            stock_symbol: Stock ticker
        
        Returns:
            MLPrediction with all model outputs
        """
        
        # Get individual model predictions
        xgb_pred = self._predict_xgboost(stock_features)
        lgb_pred = self._predict_lgb(stock_features)
        lstm_pred = self._predict_lstm(stock_features)
        rf_pred = self._predict_random_forest(stock_features)
        
        # Ensemble combination
        direction_prob = (
            xgb_pred * self.model_weights['xgboost'] +
            lgb_pred * self.model_weights['lgb'] +
            lstm_pred * self.model_weights['lstm'] +
            rf_pred * self.model_weights['rf']
        )
        
        # Model agreement
        predictions = [xgb_pred, lgb_pred, lstm_pred, rf_pred]
        model_agreement = 1 - np.std(predictions)
        
        # Determine direction
        if direction_prob > 0.55:
            predicted_direction = 'up'
        elif direction_prob < 0.45:
            predicted_direction = 'down'
        else:
            predicted_direction = 'neutral'
        
        # Calculate expected returns and probabilities
        expected_return_pct = (direction_prob - 0.5) * 10  # Scale to -5% to +5%
        
        p_5pct = self._estimate_probability(direction_prob, 0.05)
        p_8pct = self._estimate_probability(direction_prob, 0.08)
        p_12pct = self._estimate_probability(direction_prob, 0.12)
        p_15pct = self._estimate_probability(direction_prob, 0.15)
        p_20pct = self._estimate_probability(direction_prob, 0.20)
        
        expected_downside_pct = (1 - direction_prob) * 5
        
        prediction_confidence = max(abs(direction_prob - 0.5) * 2, 0.5)
        
        return MLPrediction(
            timestamp=pd.Timestamp.now().isoformat(),
            stock_symbol=stock_symbol,
            direction_probability=direction_prob,
            predicted_direction=predicted_direction,
            expected_return_pct=expected_return_pct,
            p_5pct=p_5pct,
            p_8pct=p_8pct,
            p_12pct=p_12pct,
            p_15pct=p_15pct,
            p_20pct=p_20pct,
            expected_downside_pct=expected_downside_pct,
            prediction_confidence=prediction_confidence,
            model_agreement=model_agreement,
            xgboost_direction=xgb_pred,
            lgb_direction=lgb_pred,
            lstm_direction=lstm_pred,
            rf_direction=rf_pred
        )
    
    def _predict_xgboost(self, features: pd.DataFrame) -> float:
        """XGBoost prediction (0-1 for up direction)."""
        try:
            import xgboost as xgb
            # Placeholder: in production, load actual trained model
            # return self.xgb_model.predict_proba(features)[0][1]
            logger.debug("XGBoost prediction called")
            return 0.5  # Placeholder
        except Exception as e:
            logger.warning(f"XGBoost prediction error: {str(e)}")
            return 0.5
    
    def _predict_lgb(self, features: pd.DataFrame) -> float:
        """LightGBM prediction (0-1 for up direction)."""
        try:
            import lightgbm as lgb
            logger.debug("LightGBM prediction called")
            return 0.5  # Placeholder
        except Exception as e:
            logger.warning(f"LightGBM prediction error: {str(e)}")
            return 0.5
    
    def _predict_lstm(self, features: pd.DataFrame) -> float:
        """LSTM prediction (0-1 for up direction)."""
        try:
            import tensorflow as tf
            logger.debug("LSTM prediction called")
            return 0.5  # Placeholder
        except Exception as e:
            logger.warning(f"LSTM prediction error: {str(e)}")
            return 0.5
    
    def _predict_random_forest(self, features: pd.DataFrame) -> float:
        """Random Forest prediction (0-1 for up direction)."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            logger.debug("Random Forest prediction called")
            return 0.5  # Placeholder
        except Exception as e:
            logger.warning(f"Random Forest prediction error: {str(e)}")
            return 0.5
    
    def _estimate_probability(self, direction_prob: float, target_move: float) -> float:
        """
        Estimate probability of achieving target move.
        
        Args:
            direction_prob: Base direction probability (0-1)
            target_move: Target move as decimal (0.12 = 12%)
        
        Returns:
            Probability of achieving target move
        """
        # Simplified: larger moves are less likely
        # Adjust probability based on move magnitude
        move_difficulty = min(target_move * 2, 1.0)  # Larger moves are harder
        
        # If direction is bullish, return probability; if bearish, reduce it
        if direction_prob > 0.5:
            return direction_prob * (1 - move_difficulty * 0.5)
        else:
            return (1 - direction_prob) * (1 - move_difficulty * 0.5)
