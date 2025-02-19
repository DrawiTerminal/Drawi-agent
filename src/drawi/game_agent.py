import random
import json
import os
from datetime import datetime, timedelta
import logging
import uuid

from drawi.tools import post_tweet, find_answers_with_conversation_id, reply_to_tweet
from drawi.configuration import Configuration
from drawi.utils import load_chat_model, extract_solana_addresses
from pydantic import BaseModel, Field 
from solders.pubkey import Pubkey 

# Define the game types - added new creative game types
GAME_TYPES = [
    "fun_fact",
    "emoji_story",
    "best_joke",
    "random_wallet",
    "improv_story",         
    "abstract_poetry",    
    "creative_challenge"   
]

def is_valid_solana_wallet(address: str) -> bool:
    try:
        Pubkey(address)
        return True
    except Exception:
        return False

# Function to choose a random game
def choose_game() -> tuple[str, str]:
    """
    Randomly choose a game type and compose the tweet text.
    
    Returns:
        (game_type, tweet_text)
    """
    game_type = random.choice([
        "fun_fact",
        "emoji_story",
        "best_joke",
        "random_wallet",
        "improv_story",
        "abstract_poetry",
        "creative_challenge"
    ])
    # Use custom formatted game bodies with a placeholder for result time
    if game_type == "improv_story":
        body = (
            "🎀 /GAME OPEN 🎀\n"
            "🌷 /GAME: Improve Story\n"
            "🌸 /REPLY: Complete the story: “Once upon a time…\n"
            "💒 /RULE: The most imaginative continuation wins.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    elif game_type == "fun_fact":
        body = (
            "🎀 /GAME OPEN 🎀\n"
            "🌷 /GAME: Fun Fact\n"
            "🌸 /REPLY: An interesting and little-known fact.\n"
            "💒 /RULE: The most fascinating fact wins.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    elif game_type == "emoji_story":
        body = (
            "🎀 /GAME OPEN 🎀\n"
            "🌷 /GAME: Emoji Story\n"
            "🌸 /REPLY: With a short story using only emojis.\n"
            "💒 /RULE: The most creative emoji story wins.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    elif game_type == "best_joke":
        body = (
            "🎀 /GAME OPEN 🎮\n"
            "🌷 /GAME: Best Joke\n"
            "🌸 /REPLY: Your best joke.\n"
            "💒 /RULE: The best joke wins.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    elif game_type == "abstract_poetry":
        body = (
            "🎀 /GAME OPEN 🎀\n"
            "🌷 /GAME: Abstract Poetry\n"
            "🌸 /REPLY: Complete the poem: “Under neon moons, the meme…\n"
            "💒 /RULE: The best poetic expression wins.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    elif game_type == "creative_challenge":
        body = (
            "🎀 /GAME OPEN 🎀\n"
            "🌷 /GAME: Creative Challenge\n"
            "🌸 /REPLY: Propose your unique challenge.\n"
            "💒 /RULE: The most intriguing challenge wins.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    elif game_type == "random_wallet":
        body = (
            "🎀 /GAME OPEN 🎀\n"
            "🌷 /GAME: Random Wallet\n"
            "🌸 /REPLY: Submit your Solana wallet address.\n"
            "💒 /RULE: A random selection will determine the winner.\n"
            "💌 /INCLUDE: Your Solana wallet address.\n"
            "💝 /PRIZE: 0.1 SOL.\n"
            "🦩 /RESULT: {result_time}"
        )
    else:
        body = "Game type not recognized."
    return game_type, body

class WinnerResult(BaseModel):
    wallet: str = Field(..., description="Winner wallet address")
    reply_id: str = Field(..., description="Reply ID of the winner")

class WinnerResponse(BaseModel):
    result: WinnerResult = Field(..., description="Selected winner's details")
    chain_of_thought: str = Field(..., description="Explanation of the decision process")


async def select_winner_llm(game_type: str, entries: list[dict], config: Configuration) -> dict:
    """
    Use the LLM to select the winning entry with structured output.
    
    Returns a dict with keys:
      "result": an object with keys "wallet" and "reply_id"
      "chain_of_thought": a text string explaining the decision.
    """
    model = load_chat_model(config.model)
    
    instructions = ""
    if game_type == "fun_fact":
        instructions = "pick the entry with the most interesting fact."
    elif game_type == "emoji_story":
        instructions = "pick the entry with the most creative emoji story."
    elif game_type == "fastest_reply":
        instructions = "pick the first valid entry, simulating the fastest reply."
    elif game_type == "best_joke":
        instructions = "pick the entry with the best joke."
    elif game_type == "random_wallet":
        instructions = "pick one entry at random, simulating a random selection. don't care about the content. it just needs to be random"
    elif game_type == "improv_story":
        instructions = "pick the entry with the most imaginative story continuation."
    elif game_type == "abstract_poetry":
        instructions = "pick the entry with the best poetic expression."
    elif game_type == "creative_challenge":
        instructions = "pick the entry with the most intriguing creative challenge."
    else:
        instructions = "pick one entry."
    
    context = (
        "Context: This is a game where many players participate by replying with creative answers "
        "and their wallet addresses. Your role is to evaluate each response with focus on creativity, "
        "emotion, and adherence to game rules."
    )
    
    prompt = (
        f"{context}\n"
        f"You are a fair and witty game judge. Given the following list of reply entries in JSON format:\n"
        f"{json.dumps(entries)}\n"
        f"For game type '{game_type}', {instructions}\n"
    )
    
    # Bind the defined Pydantic schema to the model using with_structured_output
    structured_model = model.with_structured_output(WinnerResponse)
    response = await structured_model.ainvoke(prompt)
    try:
        return response  # response is a WinnerResponse Pydantic object (dict-like)
    except Exception as e:
        # Fallback: choose the first valid entry with a generic explanation.
        return {
            "result": entries[0],
            "chain_of_thought": "Fallback: selected the first valid entry due to error parsing LLM output." ##TODO Change this to not select the first entry
        }

def close_game_no_winner(game: dict, post_announcement: dict, game_store) -> None:
    """
    Update the game store to mark the game as closed with no winner.
    """
    game_store.update_game(game["game_id"], {
        "status": "closed",
        "winner_tweet_id": post_announcement.get("id", ""),
        "winner_wallet": "",
        "chain_of_thought": "",
        "winning_tweet_text": ""
    })

async def run_close_game_agent_task(config: Configuration) -> None:
    """
    Process open games that have reached their close time:
      - Fetch replies, select a winner (if any), or close the game with no winner.
    """
    from drawi.game_store import GameStore
    game_store = GameStore()
    
    open_games = game_store.list_open_games()
    for game in open_games:
        close_at = game.get("close_at")
        if not close_at or datetime.now() < close_at:
            continue  # Skip games not yet ready to close
        
        logging.info(f"Processing game closure for game_id={game['game_id']}")
        tweet_id = game['tweet_id']
        replies = await find_answers_with_conversation_id(tweet_id, config=config)

        # Handle errors from reply fetching: log error and skip closing the game
        if replies and isinstance(replies, list) and replies[0].get("error"):
            error_message = replies[0]["error"]
            if "429" in error_message:
                logging.error(f"Rate limit reached for game {game['game_id']}: {error_message}")
            else:
                logging.error(f"Error fetching replies for game {game['game_id']}: {error_message}")
            continue 

        # If no replies, close game with no winner.
        if not replies:
            logging.info(f"No replies found for game_id {game['game_id']}. Closing game with no winner.")
            announcement = (
                "🎮 GAME CLOSED 🎮\n\n"
                "⚠️ NO REPLIES RECEIVED.\n"
                "😢 NO WINNER DECLARED."
            )
            post_announcement = await reply_to_tweet(tweet_id=game["tweet_id"], text=announcement, config=config)
            close_game_no_winner(game, post_announcement, game_store)
            continue

        logging.info(f"Replies received for game_id {game['game_id']}: {len(replies)}")
        valid_entries = []
        for reply in replies:
            content = reply.get("text", "")

            # Use extract_solana_addresses to find wallet addresses in the reply
            addresses = extract_solana_addresses(content)
            if addresses:
                valid_entries.append({
                    "wallet": next(iter(addresses)),  # use the first valid address found
                    "text": content,
                    "reply_id": reply.get("id"),
                    "author": reply.get("author", {})  # Store author details
                })

        # If no valid wallet addresses, close game with no winner.
        if not valid_entries:
            logging.info(f"No valid wallet addresses found for game_id {game['game_id']}. Closing game with no winner.")
            announcement = (
                "🎮 GAME CLOSED 🎮\n\n"
                "⚠️ NO VALID WALLET FOUND.\n"
                "🙁 PLEASE INCLUDE YOUR SOLANA WALLET ADDRESS NEXT TIME."
            )
            post_announcement = await reply_to_tweet(tweet_id=game["tweet_id"], text=announcement, config=config)
            close_game_no_winner(game, post_announcement, game_store)
            continue

        # If valid entries exist, select a winner using the LLM.
        winner = await select_winner_llm(game["game_type"], valid_entries, config)
        logging.info(f"Winner selected for game_id {game['game_id']}: {winner}")
        if winner.result.wallet.strip() == "":
            announcement = (
                "🎮 GAME CLOSED 🎮\n\n"
                "😞 NO IMPRESSIVE SUBMISSION RECEIVED.\n"
                "🙁 NO WINNER DECLARED, BETTER LUCK NEXT TIME!"
            )
        else:
            announcement = (
                "🎮 GAME CLOSED 🎮\n\n"
                "🏆 WINNER ANNOUNCED:\n"
                f"👉 Wallet: {winner.result.wallet}\n\n"
                "🎉 CONGRATULATIONS!"
            )
        
        post_announcement = await reply_to_tweet(tweet_id=game["tweet_id"], text=announcement, config=config)
        if "error" in post_announcement:
            logging.error(f"Error posting announcement for game_id {game['game_id']}: {post_announcement['error']}")
        else:
            winner_tweet_id = post_announcement.get("id")
            winning_entry = next((entry for entry in valid_entries if entry["reply_id"] == winner.result.reply_id), {})

            # Extract additional author fields from the winning entry.
            author = winning_entry.get("author", {})
            winner_username = author.get("username", "")
            winner_name     = author.get("name", "")
            winner_image_url = author.get("profile_image_url", "")
            winner_is_verified = author.get("verified", False)
            game_store.update_game(game["game_id"], {
                "status": "closed",
                "winner_tweet_id": winner_tweet_id,
                "winner_wallet": winner.result.wallet,
                "chain_of_thought": winner.chain_of_thought,
                "winning_tweet_text": winning_entry.get("text", ""),
                "winner_username": winner_username,
                "winner_name": winner_name,
                "winner_image_url": winner_image_url,
                "winner_author_id": winning_entry.get("author_id", ""),
                "winner_is_verified": winner_is_verified
            })
            logging.info(f"Game {game['game_id']} updated with winner information")

async def run_create_game_agent_task(config: Configuration) -> None:
    """
    Create a new game:
      - Choose a game type, post an open tweet, and store it in the database.
    """
    from drawi.game_store import GameStore
    game_type, tweet_text = choose_game()
    
    logging.info(f"Creating new game of type: {game_type} at {datetime.now()}")
    post_result = await post_tweet(text=tweet_text, config=config)
    if "error" in post_result:
        logging.error(f"Error posting new game tweet: {post_result['error']}")
        return
    tweet_id = post_result.get("id")
    if not tweet_id:
        logging.error("No tweet id returned for new game; aborting game creation.")
        return
    
    # Determine game duration using the environment variable, else choose random.
    game_duration_env = os.getenv("GAME_DURATION")
    if game_duration_env and game_duration_env.strip() != "":
        game_duration = int(game_duration_env)
        # GAME_DURATION is in seconds; display duration in minutes.
        display_minutes = game_duration // 60
        tweet_text = tweet_text.format(result_time=f"In {display_minutes} minutes.")
        close_at = datetime.now() + timedelta(seconds=game_duration)
    else:
        possible_durations = [30, 60, 90, 120, 150, 180]
        random_minutes = random.choice(possible_durations)
        tweet_text = tweet_text.format(result_time=f"In {random_minutes} minutes.")
        close_at = datetime.now() + timedelta(minutes=random_minutes)
    
    logging.info(f"New game tweet posted: {game_type}, id: {tweet_id}, closing at {close_at}")
    
    game_store = GameStore()
    game_id = str(uuid.uuid4())
    game_store.create_game(game_id, tweet_id, game_type, close_at)

# Optionally, you can keep a simple combined function to run both tasks sequentially:
async def run_game_agent_cycle(config: Configuration) -> None:
    await run_close_game_agent_task(config)
    await run_create_game_agent_task(config)
