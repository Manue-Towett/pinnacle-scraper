from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Depends

from . import models, crud, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.post("/league/", response_model=schemas.League)
def create_league(league: schemas.LeagueCreate, db: Session=Depends(get_db)):
    db_league = crud.get_league_by_name(db, name=league.name)

    if db_league:
        return db_league
        # raise HTTPException(status_code=400, detail="League already registered")
    
    return crud.create_league(db=db, league=league)

@app.get("/leagues/", response_model=list[schemas.League])
def get_leagues(db: Session=Depends(get_db)):
    leagues = crud.get_leagues(db=db)

    return leagues

@app.get("/game/{game_id}", response_model=schemas.Game)
def get_game(game_id: int, db:Session=Depends(get_db)):
    game = crud.get_game(db=db, game_id=game_id)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game

@app.post("/{league}/games/", response_model=list[schemas.Game])
def create_games(league:str, games:list[schemas.GameCreate], db:Session=Depends(get_db)):
    db_league = crud.get_league_by_name(db, name=league)

    unique = []

    [unique.append(g) for g in games if not crud.game_exists(db, game=g)]

    if not len(unique):
        db_games = crud.get_games_by_teams(db=db, r_games=games)

        return db_games
        # raise HTTPException(status_code=400, detail="No unique games")

    db_games = crud.create_games(db=db, games=unique, league=db_league)

    return db_games

@app.post("/odds", response_model=list[schemas.PinnacleOdds])
def create_odds(odds:list[schemas.PinnacleOddsCreate], db:Session=Depends(get_db)):
    db_odds = crud.create_pinnacle_odds(db=db, odds=odds)

    return db_odds

# @app.get("/delete")
# def delete(league:str, db:Session=Depends(get_db)):
#     crud.delete_league(db=db, league=league)

#     return {"message": "ok"}