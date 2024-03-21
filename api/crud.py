from typing import List

from sqlalchemy.orm import Session

from . import models, schemas

def get_league(db: Session, league_id: int):
    return db.query(models.League).filter(models.League.id==league_id).first()

def get_leagues(db: Session):
    return db.query(models.League).all()

def create_league(db: Session, league: schemas.League):
    db_league = models.League(name=league.name)
    db.add(db_league)
    db.commit()
    db.refresh(db_league)
    return db_league

def get_league_by_name(db: Session, name: str) -> models.League:
    return db.query(models.League).filter(models.League.name==name).first()

def get_game(db: Session, game_id:int):
    return db.query(models.Game).filter(models.Game.id==game_id).first()

def game_exists(db:Session, game: schemas.GameCreate):
    return db.query(models.Game).filter(models.Game.home_team==game.home_team,
                                        models.Game.away_team==game.away_team,
                                        models.Game.start_time==game.start_time).first()

def get_games_by_teams(db:Session, r_games:list[schemas.GameCreate]):
    return [db.query(models.Game).filter(models.Game.home_team==g.home_team,
                                         models.Game.away_team==g.away_team,
                                         models.Game.start_time==g.start_time).first() for g in r_games]

def get_games_by_start_time(db: Session, start_time: str) -> List[models.Game]:
    return db.query(models.Game).filter(models.Game.start_time==start_time).all()

def create_games(db: Session, games:list[schemas.Game], league: models.League):
    db_games = [models.Game(**g.model_dump(), league_id=league.id) for g in games]
    db.add_all(db_games)
    db.commit()
    [db.refresh(db_game) for db_game in db_games]
    return db_games

def get_pinnacle_odds(db: Session, odds_id: str):
    return db.query(models.PinnacleOdds).filter(models.PinnacleOdds.id==odds_id).first()

def get_pinnacle_odds_by_league(db: Session, league: str) -> List[models.PinnacleOdds]:
    league = db.query(models.League).filter(models.League.name==league).first()

    return db.query(models.PinnacleOdds).filter(
                        models.PinnacleOdds.league_id==league.id).all()

def create_pinnacle_odds(db: Session, odds:list[schemas.PinnacleOddsCreate]):
    unique_odds, pinnacle_odds = [], []

    for odd in odds:
        pinnacle_odd = db.query(models.PinnacleOdds).filter(
                            models.PinnacleOdds.game_id==odd.game_id).first()
        
        if pinnacle_odd is not None:
            pinnacle_odd.home_total = odd.home_total
            pinnacle_odd.away_total = odd.away_total
            pinnacle_odd.away_spread = odd.away_spread
            pinnacle_odd.home_spread = odd.home_spread

            db.commit()
            db.refresh(pinnacle_odd)

            pinnacle_odds.append(pinnacle_odd)

            continue
        
        game = db.query(models.Game).filter(models.Game.id==odd.game_id).first()

        pinnacle_odd = models.PinnacleOdds(**odd.model_dump(), league_id=game.league_id)

        unique_odds.append(pinnacle_odd)
        pinnacle_odds.append(pinnacle_odd)

    db.add_all(unique_odds)
    db.commit()
    [db.refresh(unique_odd) for unique_odd in pinnacle_odds]

    return pinnacle_odds

def delete_league(db:Session, league:str):
    leagues = db.query(models.League).filter(models.League.name==league).all()

    [db.delete(l) for l in leagues]
    db.commit()