import re
import time
import json
import dataclasses
from typing import Optional, Tuple

import requests

from utils import Logger

HEADERS = {
    'authority': 'guest.api.arcadia.pinnacle.com',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'dnt': '1',
    'origin': 'https://www.pinnacle.com',
    'referer': 'https://www.pinnacle.com/',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'x-api-key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
    'x-device-uuid': 'f14b632b-febf2aca-43019d99-82ff4ddb',
}

API_HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

PARAMS = {
    'brandId': '0',
}

BASE_URL = 'https://guest.api.arcadia.pinnacle.com{}'

BASE_API_URL = "http://127.0.0.1:8000{}"

SPORTS_URI = "/0.1/sports?brandId=0"

MATCHUPS_URI = "/0.1/leagues/{}/matchups"

LEAGUES_URI = "/0.1/sports/{}/leagues?all=false&brandId=0"

ODDS_URI = "/0.1/leagues/{}/markets/straight"

SPORT_MAPPINGS = {"baseball": ["MLB"],
                  "hockey": ["NHL"],
                  "basketball": ["NBA", "NCAAB"],
                  "football": ["NFL", "NCAAF"]}

@dataclasses.dataclass
class Game:
    game_id: int
    home_team: str
    away_team: str
    has_markets: bool
    start_time: str

@dataclasses.dataclass
class Games:
    games: list[Game]=dataclasses.field(default_factory=list)

@dataclasses.dataclass
class Odds:
    game: Game
    home_spread: float
    away_spread: float
    home_total: str
    away_total: str

@dataclasses.dataclass
class LeagueOdds:
    league: str
    game_odds: list[Odds]=dataclasses.field(default_factory=list)

@dataclasses.dataclass
class PinnacleOdd:
    odd_dict: dict
    matchup_id: int = None
    odd_type: str = None
    cuttoff_time: str = None
    home_team_odd: float|int = None
    away_team_odd: float|int = None

    def __post_init__(self) -> None:
        self.matchup_id: int = self.odd_dict["matchupId"]
        self.odd_type: str = self.odd_dict["type"]
        self.cuttoff_time: str = self.odd_dict["cutoffAt"]

        odd_a, odd_b = self.odd_dict["prices"] if len(self.odd_dict["prices"])==2 else [{}, {}]

        if not odd_a.get("points") and not odd_b.get("designation") \
            and not odd_a.get("designation"): return

        try:
            odd_a_des, odd_b_des = odd_a["designation"], odd_b["designation"]

            self.home_team_odd: float|int = odd_a["points"] if odd_a_des=="home" else odd_b["points"]
            self.away_team_odd: float|int = odd_b["points"] if odd_b_des=="away" else odd_a["points"]
        except: pass

        self.odd_dict = None

@dataclasses.dataclass
class PinnacleOdds:
    pinnacle_odds: list[PinnacleOdd]=dataclasses.field(default_factory=list)

class PinnacleScraper:
    """Scrapes odds from https://www.pinnacle.com"""  
    def __init__(self) -> None:
        self.logger = Logger(__class__.__name__)
        self.logger.info("{:*^50}".format(f"{__class__.__name__} Started"))

    def __get_request(self, uri: str, params: Optional[dict]=None) -> list[dict]:
        resource_url = BASE_URL.format(uri)

        while True:
            try:
                response = requests.get(resource_url, headers=HEADERS, params=params)

                if response.ok: return response.json()

            except: pass

    def __get_league_uri(self, league: str) -> Optional[str]:
        response = self.__get_request(SPORTS_URI)

        for k, v in SPORT_MAPPINGS.items():
            if not league in v: continue
            
            for sport in response:
                if not re.match(rf"{k}", sport["name"], re.I): continue

                return LEAGUES_URI.format(sport["id"])
    
    def __get_pinnacle_league(self, league: str, leagues_uri: str) -> Optional[Tuple[str, str]]:
        response = self.__get_request(leagues_uri)

        for pinnacle_league in response:
            p_league = pinnacle_league["name"]

            if not re.match(rf"{p_league}", league, re.I): continue

            league_id = pinnacle_league["id"]

            return MATCHUPS_URI.format(league_id), ODDS_URI.format(league_id) 
    
    def __get_pinnacle_matchups(self, matchup_uri: str) -> Games:
        games = Games() 

        for matchup in self.__get_request(matchup_uri, params=PARAMS):
            parent = matchup["parent"]
            participants = parent.get("participants") if parent is not None else None

            if isinstance(parent, dict) and participants and len(participants)==2:
                team_a, team_b = parent["participants"]
                team_a_alig = parent["participants"][0]["alignment"]
            else:
                if len(matchup["participants"]) != 2: continue

                team_a, team_b = matchup["participants"]
                team_a_alig = matchup["participants"][0]["alignment"]

            games.games.append(
                Game(game_id=matchup["id"],
                     home_team=team_a["name"] if team_a_alig=="home" else team_b["name"],
                     away_team=team_a["name"] if team_a_alig!="home" else team_b["name"],
                     has_markets=matchup["hasMarkets"],
                     start_time=matchup["startTime"]))
        
        return games
    
    @staticmethod
    def __process_games_and_odds(league: str, games: Games, p_odds: PinnacleOdds) -> LeagueOdds:
        pinnacle_odds, odds = p_odds.pinnacle_odds, LeagueOdds(league)

        for game in games.games:
            odd = Odds(game=game, home_spread=None, away_spread=None, home_total=None, away_total=None)

            found = False

            for pinnacle_odd in pinnacle_odds:
                if pinnacle_odd.matchup_id == game.game_id:
                    found = True

                    if pinnacle_odd.odd_type == "total":
                        odd.home_total = pinnacle_odd.home_team_odd
                        odd.away_total = pinnacle_odd.away_team_odd
                    
                    elif pinnacle_odd.odd_type == "spread":
                        odd.home_spread = pinnacle_odd.home_team_odd
                        odd.away_spread = pinnacle_odd.away_team_odd
            
            if found and isinstance(odd.home_spread, (int, float)): 
                is_home_fav = odd.home_spread < 0
                odd.home_total = f"u{odd.home_total}" if is_home_fav else f"o{odd.home_total}"
                odd.away_total = f"o{odd.away_total}" if is_home_fav else f"u{odd.away_total}"
                odds.game_odds.append(odd)
        
        return odds
    
    def __get_pinnacle_odds(self, odds_uri: str) -> PinnacleOdds:
        markets = self.__get_request(odds_uri)

        odds = []

        for market in markets:
            is_alternate = market.get("isAlternate")

            if market.get("period"): continue

            if is_alternate is not None and not is_alternate: odds.append(market)
        
        pinnacle_odds = PinnacleOdds()

        [pinnacle_odds.pinnacle_odds.append(PinnacleOdd(odd)) for odd in odds]

        return pinnacle_odds
    
    def __save_to_json(self, data: LeagueOdds, league: str) -> None:
        with open(f"./data/{league}.json", "w") as f:
            json.dump(dataclasses.asdict(data), f, indent=4)
    
    def __api_get(self, uri: str, params:Optional[dict]=None) -> requests.Response:
        headers, url = {'Content-Type': 'application/json'}, BASE_API_URL.format(uri)

        while True:
            try:
                response = requests.get(url, headers=headers, params=params)

                if response.ok:
                    return response
                
            except: pass
    
    def __api_post(self, uri:str, payload:Optional[dict|list[dict]]) -> requests.Response:
        url = BASE_API_URL.format(uri)

        while True:
            try:
                response = requests.post(url, headers=API_HEADERS, json=payload)

                if response.ok:
                    return response
            
            except: pass
    
    def __save_games_to_db(self, leage_odds: LeagueOdds) -> None:
        api_league = self.__api_post("/league/", {"name": leage_odds.league})

        games = [
            {'home_team': game_odd.game.home_team,
              'away_team': game_odd.game.away_team,
              'has_markets': game_odd.game.has_markets,
              'start_time': game_odd.game.start_time} for game_odd in leage_odds.game_odds]
        
        api_games = self.__api_post(f"/{api_league.json()['name']}/games/", games)

        self.__save_odds_to_db(leage_odds.game_odds, api_games.json())

    def __save_odds_to_db(self, p_odds: list[Odds], api_games: list[dict]) -> None:
        odds = []

        for p_odd in p_odds:
            for api_game in api_games:
                if api_game["home_team"]==p_odd.game.home_team \
                    and api_game["away_team"]==p_odd.game.away_team \
                        and api_game['start_time']==p_odd.game.start_time:
                    odds.append({"game_id": api_game["id"],
                                 "home_total": p_odd.home_total,
                                 "away_total": p_odd.away_total,
                                 "home_spread": p_odd.home_spread,
                                 "away_spread": p_odd.away_spread})
                    
                    break
        
        if len(odds): self.__api_post("/odds", odds)        
     
    def run(self, league: str) -> None:
        leagues_uri = self.__get_league_uri(league)

        matchup_uri, odds_uri = self.__get_pinnacle_league(league, leagues_uri)

        games = self.__get_pinnacle_matchups(matchup_uri)

        pinnacle_odds = self.__get_pinnacle_odds(odds_uri)

        odds = self.__process_games_and_odds(league, games, pinnacle_odds)

        self.logger.info("Saving {} odds for {}".format(len(odds.game_odds), league))

        # self.__save_to_json(odds, league)  
        self.__save_games_to_db(odds) 

        self.logger.info("Odds saved for {}".format(league))

        return dataclasses.asdict(odds)     

if __name__ == "__main__":
    leagues = ["NBA", "NHL", "MLB", "NCAAB", "NCAAF"]

    app = PinnacleScraper()

    while True:
        odds = []

        for league in leagues:
            try:odds.append(app.run(league))
            except Exception as e: 
                print(e)
                break

            time.sleep(2)
        
        time.sleep(120)