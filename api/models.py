from sqlalchemy.orm import relationship
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float

from .database import Base

class League(Base):
    __tablename__ = "league"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)

    games = relationship("Game", back_populates="league", cascade="all,delete")
    odds = relationship("PinnacleOdds", back_populates="league", cascade="all,delete")

class Game(Base):
    __tablename__ = "game"

    id = Column(Integer, primary_key=True, autoincrement=True)
    home_team = Column(String, index=True)
    away_team = Column(String, index=True)
    has_markets = Column(Boolean, index=True)
    start_time = Column(String, index=True)
    league_id = Column(Integer, ForeignKey("league.id"))

    league = relationship("League", back_populates="games", cascade="all,delete")
    odds = relationship("PinnacleOdds", back_populates="game", cascade="all,delete")

class PinnacleOdds(Base):
    __tablename__ = "pinnacle_odds"

    id = Column(Integer, primary_key=True)
    home_spread = Column(Float, index=True)
    away_spread = Column(Float, index=True)
    home_total = Column(String, index=True)
    away_total = Column(String, index=True)
    game_id = Column(Integer, ForeignKey("game.id"))
    league_id = Column(Integer, ForeignKey("league.id"))

    game = relationship("Game", back_populates="odds", cascade="all, delete")
    league = relationship("League", back_populates="odds", cascade="all,delete")