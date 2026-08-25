# Add BaseModel import
from pydantic import BaseModel

# Signal Package Init
from .quality_scorer import SignalQualityScorer, SignalQualityOutput
from .entry_optimizer import EntryOptimizer, EntryOutput, EntryType
from .stop_loss_optimizer import StopLossOptimizer, StopLossOutput
from .target_optimizer import TargetOptimizer, TargetOutput
from .target_space import TargetSpaceAnalyzer, TargetSpaceOutput, TargetScenario
from .risk_reward import RiskRewardCalculator, RiskRewardOutput
from .signal_generator import SignalGenerator, TradeSignalOutput

__all__ = [
    'SignalQualityScorer',
    'SignalQualityOutput',
    'EntryOptimizer',
    'EntryOutput',
    'EntryType',
    'StopLossOptimizer',
    'StopLossOutput',
    'TargetOptimizer',
    'TargetOutput',
    'TargetSpaceAnalyzer',
    'TargetSpaceOutput',
    'TargetScenario',
    'RiskRewardCalculator',
    'RiskRewardOutput',
    'SignalGenerator',
    'TradeSignalOutput'
]
