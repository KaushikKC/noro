"""
Trading tools for calculating optimal positions
"""
import json
from typing import Dict, Any

try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    # Fallback for when spoon-ai-sdk is not installed
    class BaseTool:
        pass


def kelly_criterion(probability: float, odds: float, bankroll: float = 1000.0) -> float:
    """
    Calculate Kelly Criterion stake
    
    Args:
        probability: Probability of winning (0-1)
        odds: Decimal odds (e.g., 2.0 for even money)
        bankroll: Total available capital
        
    Returns:
        Recommended stake amount
    """
    if probability <= 0 or probability >= 1:
        return 0.0
    
    if odds <= 1.0:
        return 0.0
    
    # Kelly formula: f = (p * b - q) / b
    # where f = fraction of bankroll, p = probability, b = odds - 1, q = 1 - p
    b = odds - 1.0
    q = 1.0 - probability
    f = (probability * b - q) / b
    
    # Fractional Kelly (use 25% of full Kelly for safety)
    f = f * 0.25
    
    # Ensure non-negative and within bankroll
    stake = max(0.0, min(f * bankroll, bankroll * 0.1))  # Cap at 10% of bankroll
    
    return round(stake, 2)


def calculate_confidence_stake(probability: float, confidence: float, base_stake: float = 100.0) -> float:
    """
    Calculate stake based on confidence level
    
    Args:
        probability: Probability of outcome (0-1)
        confidence: Confidence in the analysis (0-1)
        base_stake: Base stake amount
        
    Returns:
        Recommended stake amount
    """
    # Adjust stake based on how far probability is from 0.5
    probability_confidence = abs(probability - 0.5) * 2  # 0 to 1
    
    # Combine probability confidence with analysis confidence
    combined_confidence = (probability_confidence + confidence) / 2
    
    # Scale stake by combined confidence
    stake = base_stake * combined_confidence
    
    return round(stake, 2)


class KellyCriterionTool(BaseTool):
    """Tool for calculating optimal stake using Kelly Criterion"""
    
    name: str = "kelly_criterion_calc"
    description: str = "Calculate optimal stake size using Kelly Criterion based on probability and odds. Returns recommended stake amount."
    parameters: dict = {
        "type": "object",
        "properties": {
            "probability": {
                "type": "number",
                "description": "Probability of winning (0-1)"
            },
            "odds": {
                "type": "number",
                "description": "Decimal odds (e.g., 2.0 for even money)"
            },
            "bankroll": {
                "type": "number",
                "description": "Total available capital (default: 1000)",
                "default": 1000.0
            }
        },
        "required": ["probability", "odds"]
    }
    
    async def execute(self, probability: float, odds: float, bankroll: float = 1000.0) -> str:
        """
        Calculate Kelly Criterion stake
        
        Args:
            probability: Probability of winning
            odds: Decimal odds
            bankroll: Total capital
            
        Returns:
            JSON string with stake recommendation
        """
        stake = kelly_criterion(probability, odds, bankroll)
        return json.dumps({
            "stake": stake,
            "probability": probability,
            "odds": odds,
            "bankroll": bankroll,
            "stake_percentage": round((stake / bankroll) * 100, 2) if bankroll > 0 else 0
        }, indent=2)


class ConfidenceStakeTool(BaseTool):
    """Tool for calculating stake based on confidence"""
    
    name: str = "confidence_stake_calc"
    description: str = "Calculate stake size based on probability and confidence level. Simpler alternative to Kelly Criterion."
    parameters: dict = {
        "type": "object",
        "properties": {
            "probability": {
                "type": "number",
                "description": "Probability of outcome (0-1)"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence in the analysis (0-1)"
            },
            "base_stake": {
                "type": "number",
                "description": "Base stake amount (default: 100)",
                "default": 100.0
            }
        },
        "required": ["probability", "confidence"]
    }
    
    async def execute(self, probability: float, confidence: float, base_stake: float = 100.0) -> str:
        """
        Calculate confidence-based stake
        
        Args:
            probability: Probability of outcome
            confidence: Confidence level
            base_stake: Base stake amount
            
        Returns:
            JSON string with stake recommendation
        """
        stake = calculate_confidence_stake(probability, confidence, base_stake)
        return json.dumps({
            "stake": stake,
            "probability": probability,
            "confidence": confidence,
            "base_stake": base_stake
        }, indent=2)

