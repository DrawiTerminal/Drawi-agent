"""Command line script to run the agent scheduler."""

import argparse
import asyncio
import os
import platform
import signal
import logging
import sys
from dotenv import load_dotenv

from drawi.scheduler import AgentScheduler
from drawi.configuration import Configuration

# Configure nicely formatted logs for default container management
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# logging.getLogger("pymongo").setLevel(logging.WARNING)

# Global event for shutdown coordination
stop_event = None

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the agent scheduler")
    parser.add_argument(
        "--game-interval",
        type=int,
        default=240,
        help="Seconds between game tasks (default: 240 seconds)",
    )
    return parser.parse_args()


def setup_signal_handlers(scheduler):
    """Set up signal handlers appropriate for the current platform."""
    global stop_event
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        if not stop_event.is_set():
            logging.info("Shutting down gracefully... (This may take a few seconds)")
            stop_event.set()

    # Set up platform-specific signal handling
    if platform.system() != "Windows":
        # Unix-like systems support SIGTERM
        signal.signal(signal.SIGTERM, signal_handler)

    # SIGINT (Ctrl+C) works on all platforms
    signal.signal(signal.SIGINT, signal_handler)


async def main():
    """Main entry point."""
    global stop_event

    # Load environment variables
    load_dotenv()

    # List of required environment variables
    required_env_vars = [
        "X_API_KEY",
        "X_API_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
        "X_BEARER_TOKEN",
        "X_USER_ID",
    ]

    # Check if all required environment variables are set
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        sys.exit(1)

    # Parse arguments
    args = parse_args()

    # Create configuration
    config = Configuration(
        twitter_api_key=os.getenv("X_API_KEY"),
        twitter_api_secret=os.getenv("X_API_SECRET"),
        twitter_access_token=os.getenv("X_ACCESS_TOKEN"),
        twitter_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        twitter_bearer_token=os.getenv("X_BEARER_TOKEN"),
        twitter_user_id=os.getenv("X_USER_ID"),
    )

    # Read schedule intervals from env variables (in seconds) with defaults.
    start_schedule = int(os.getenv("START_GAME_SCHEDULE", 240))
    close_schedule = int(os.getenv("CLOSE_GAME_SCHEDULE", 240))
    game_duration = int(os.getenv("GAME_DURATION", 100))  # playtime in seconds

    # Read and parse the CREATE_GAME_ON_STARTUP environment variable.
    create_game_on_startup = os.getenv("CREATE_GAME_ON_STARTUP", "true").lower() in ["true", "1", "yes"]
    # Read and parse the DISABLE_CREATE_GAME environment variable.
    disable_create_game = os.getenv("DISABLE_CREATE_GAME", "false").lower() in ["true", "1", "yes"]

    # Initialize scheduler
    scheduler = AgentScheduler(config)

    # Conditionally schedule the create game task.
    if disable_create_game:
        logging.info("DISABLE_CREATE_GAME is true. Skipping create game task scheduling.")
    else:
        scheduler.schedule_create_game(seconds=start_schedule, run_on_startup=create_game_on_startup)

    # Always schedule the close game task.
    scheduler.schedule_close_game(seconds=close_schedule)

    # Start the scheduler
    scheduler.start()

    # Set up signal handlers
    setup_signal_handlers(scheduler)

    logging.info(f"Scheduler running. Create game every {start_schedule} sec, playtime of {game_duration} sec, check for game to close every {close_schedule} sec.")

    try:
        # Wait for stop signal
        while not stop_event.is_set():
            await asyncio.sleep(1)
    finally:
        scheduler.stop()
        logging.info("Scheduler stopped successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This catches any KeyboardInterrupt that might occur during setup
        if stop_event and not stop_event.is_set():
            logging.info("Shutting down gracefully... (This may take a few seconds)")
            stop_event.set()
