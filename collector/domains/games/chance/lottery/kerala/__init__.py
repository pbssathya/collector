"""
Kerala Lottery domain.

Part of the Games of Chance → Lottery hierarchy.
"""

from .connector import Connector
from .parser import Parser
from .result import Result

__all__ = ["Connector", "Parser", "Result"]
