from pydantic import BaseModel

class PinnacleOddsBase(BaseModel):
    home_spread: float
    away_spread: float
    home_total: str
    away_total: str

class PinnacleOddsCreate(PinnacleOddsBase):
    game_id: int

class PinnacleOdds(PinnacleOddsBase):
    id: int

    class Config:
        from_attributes = True

class GameBase(BaseModel):
    home_team: str
    away_team: str
    has_markets: bool
    start_time: str

class GameCreate(GameBase):
    pass

class Game(GameBase):
    id: int
    odds: list[PinnacleOdds]

    class Config:
        from_attributes = True

class LeagueBase(BaseModel):
    name: str

class LeagueCreate(LeagueBase):
    pass

class League(LeagueBase):
    id: int
    name: str    
    games: list[Game]

    class Config:
        from_attributes = True