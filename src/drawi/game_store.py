import os
import logging
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional

class GameStore:
    def __init__(self):
        # Connect to Cosmos DB via the MongoDB API using environment variable
        mongo_uri = os.getenv("COSMOS_MONGO_URI")
        if not mongo_uri:
            raise ValueError("COSMOS_MONGO_URI is not set in the environment.")
        self.client = MongoClient(mongo_uri)
        self.db = self.client["drawi_db"]
        self.collection = self.db["games"]

    def create_game(self, game_id: str, tweet_id: str, game_type: str, close_at: datetime, status: str = "open") -> None:      
        game_doc = {
            "game_id": game_id,
            "tweet_id": tweet_id,
            "game_type": game_type,
            "title": f"Game {game_type.capitalize()}",
            "status": status,
            "created_at": datetime.now(),
            "close_at": close_at,
            "winner_tweet_id": None, 
            "winner_wallet": None
        }
        self.collection.insert_one(game_doc)
        logging.info(f"Game created in db: game_id={game_id}")

    def update_game(self, game_id: str, update_fields: dict) -> None:
        # Add updated_at field before updating
        update_fields["updated_at"] = datetime.now()
        self.collection.update_one({"game_id": game_id}, {"$set": update_fields})
        logging.info(f"Game updated in db: game_id={game_id}, fields={update_fields}")

    def list_open_games(self) -> list:
        return list(self.collection.find({"status": "open"}))