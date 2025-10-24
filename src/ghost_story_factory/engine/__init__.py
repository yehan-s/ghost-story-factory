"""Ghost Story Factory Game Engine

交互式游戏引擎核心模块
"""

from .state import GameState
from .choices import Choice, ChoiceType, ChoicePointsGenerator
from .response import RuntimeResponseGenerator
from .game_loop import GameEngine
from .intent import IntentMappingEngine, Intent, ValidationResult
from .endings import EndingSystem, EndingType, Ending

__all__ = [
    "GameState",
    "Choice",
    "ChoiceType",
    "ChoicePointsGenerator",
    "RuntimeResponseGenerator",
    "GameEngine",
    "IntentMappingEngine",
    "Intent",
    "ValidationResult",
    "EndingSystem",
    "EndingType",
    "Ending",
]

