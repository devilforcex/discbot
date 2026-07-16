"""
Facade — keeps old import path working.
Actual implementation split into bot/music/lavalink/{client,events}.py
"""

from .lavalink.client import LavalinkClient
from .lavalink.events import WavelinkEvents, setup

__all__ = ["LavalinkClient", "WavelinkEvents", "setup"]
