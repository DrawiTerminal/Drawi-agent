"""Schedule and run agent tasks periodically."""

import asyncio
from datetime import datetime, timedelta
import logging
import random
from typing import Optional, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from drawi.configuration import Configuration
from drawi.game_agent import run_create_game_agent_task, run_close_game_agent_task  # updated imports

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentScheduler:
    """Scheduler for running agent tasks periodically."""
    
    def __init__(self, config: Optional[Configuration] = None):
        """Initialize the scheduler.
        
        Args:
            config: Optional configuration override
        """
        self.config = config
        self.scheduler = AsyncIOScheduler()
        


    def schedule_create_game(self, seconds: int = 240, run_on_startup: bool = True):
        """Schedule a task to create a new game.
        
        Args:
            seconds: Seconds between creating games.
            run_on_startup: Whether to run the task immediately on startup.
        """
        next_run = datetime.now() if run_on_startup else datetime.now() + timedelta(seconds=seconds)
        self.scheduler.add_job(
            run_create_game_agent_task,
            trigger=IntervalTrigger(seconds=seconds),
            args=[self.config],
            id="create_game_job",
            replace_existing=True,
            next_run_time=next_run,
            misfire_grace_time=60  # Allow 60 sec grace period for misfires
        )
        logging.info(f"Scheduled create game task every {seconds} second(s), run_on_startup={run_on_startup}")
        
    def schedule_close_game(self, seconds: int = 240):
        """Schedule a task to close open games.
        
        Args:
            seconds: Seconds between checking for game closures.
        """
        self.scheduler.add_job(
            run_close_game_agent_task,
            trigger=IntervalTrigger(seconds=seconds),
            args=[self.config],
            id="close_game_job",
            replace_existing=True,
            next_run_time=datetime.now(),  # Trigger immediately
            misfire_grace_time=60  # Allow 60 sec grace period for misfires
        )
        logging.info(f"Scheduled close game task every {seconds} second(s)")
        
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Scheduler started")
        
    def stop(self):
        """Stop the scheduler."""
        try:
            # Shutdown with wait=True to allow current jobs to complete
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")

async def main():
    """Main entry point for running the scheduler."""
    # Initialize scheduler
    scheduler = AgentScheduler()
    scheduler.schedule_create_game(seconds=240)  # Create game task every 240 seconds
    scheduler.schedule_close_game(seconds=240)  # Close game task every 240 seconds
    
    # Start the scheduler
    scheduler.start()
    
    try:
        # Keep the script running
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
