# Drawi Agent

<table>
  <tr>
    <td style="vertical-align: top; width: 220px;">
      <img src="./static/pfp_terminal.png" alt="Drawi Agent Terminal View" width="600" />
    </td>
    <td style="vertical-align: top; padding-left: 20px;">
      Drawi Agent is a professional automated social media and game management system designed for creating, monitoring, and closing interactive game events on platforms such as X. Leveraging advanced language models and asynchronous task scheduling, Drawi Agent efficiently selects winners from creative contests and maintains a consistent social media presence.
    </td>
  </tr>
</table>

[![Integration Tests](https://github.com/langchain-ai/react-agent/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/react-agent/actions/workflows/integration-tests.yml)
[![Open in LangGraph Studio](https://img.shields.io/badge/Open_in-LangGraph_Studio-00324d.svg)](https://langgraph-studio.vercel.app/templates/open?githubUrl=https://github.com/langchain-ai/react-agent)

![Drawi Agent UI](./static/studio_ui.png)

## Table of Contents

- [Drawi Agent](#drawi-agent)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Architecture](#architecture)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Setup](#setup)
  - [Configuration](#configuration)
  - [Usage](#usage)
    - [Running the Scheduler](#running-the-scheduler)
    - [Running Individual Modules](#running-individual-modules)
  - [How to Customize](#how-to-customize)
  - [Advanced Topics](#advanced-topics)
  - [Troubleshooting](#troubleshooting)
  - [Contributing](#contributing)
  - [License](#license)

## Overview

Drawi Agent automates the lifecycle of game events:
- **Game Creation:** Automatically posts engaging game prompts to Twitter.
- **Response Collection:** Monitors replies and filters valid game entries.
- **LLM-Based Judging:** Leverages a language model within a ReAct loop to select contest winners based on creativity and engagement.
- **Game Closure:** Updates game statuses in a Cosmos DB (using MongoDB API) by marking completed events and logging winner details.

## Features

- **Automated Game Creation:** Posts game prompts at scheduled intervals.
- **Dynamic Scheduling:** Configurable game durations with environment variable overrides or randomized timings.
- **LLM-Powered Decision Making:** Uses advanced language models (Anthropic or OpenAI) for fair winner selection.
- **Database Integration:** Persists game states reliably using Cosmos DB via MongoDB API.
- **Asynchronous Task Management:** Built with APScheduler and asyncio for efficient, concurrent operations.
- **Extensibility:** Modular codebase that allows easy addition or customization of tools and game logic.
- **Robust Logging & Error Handling:** Detailed logging for system monitoring and troubleshooting.

## Architecture

Drawi Agent follows a modular architecture:
- **Scheduler Module:** Uses APScheduler to periodically trigger game creation and closure tasks.
- **Game Agent Module:** Contains the core logic for posting game prompts to Twitter, processing replies, and invoking the LLM.
- **Database Module:** Manages game state persistence, including creation, update, and querying of open games.
- **Tools Module:** Contains helper functions for API interactions (e.g., posting tweets, searching content, fetching tweets) and LLM integrations.
- **Configuration Module:** Centralizes environment variable management and API key configuration.

The overall system is designed to be scalable and easily deployable in cloud environments.

## Installation

### Prerequisites

- Python 3.8 or higher
- API keys for:
  - Twitter (API key, API secret, Access token, Access token secret, Bearer token, User ID)
  - Language model provider (Anthropic or OpenAI)
  - Cosmos DB (MongoDB connection string)

### Setup

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/drawi-agent.git
    cd drawi-agent
    ```
2. **Configure Environment Variables:**
    Copy the example file and update with your credentials:
    ```bash
    cp .env.example .env
    ```
3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Drawi Agent is highly configurable through environment variables. Key configurations include:
- **Twitter API Credentials:** `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`, `X_BEARER_TOKEN`, `X_USER_ID`
- **Game Scheduling:** `GAME_DURATION`, `START_GAME_SCHEDULE`, `CLOSE_GAME_SCHEDULE`
- **Feature Toggles:** `DISABLE_CREATE_GAME`, `CREATE_GAME_ON_STARTUP`
- **Custom Instructions:** `CUSTOM_INSTRUCTIONS`
- **Cosmos DB URI:** `COSMOS_MONGO_URI`
- **Language Model Settings:** `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, etc.

Example configuration in your `.env`:
```properties
X_API_KEY=your-twitter-api-key
X_API_SECRET=your-twitter-api-secret
X_ACCESS_TOKEN=your-twitter-access-token
X_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
X_BEARER_TOKEN=your-twitter-bearer-token
X_USER_ID=your-twitter-user-id

GAME_DURATION=1000
START_GAME_SCHEDULE=1000
CLOSE_GAME_SCHEDULE=1000
DISABLE_CREATE_GAME=false
CREATE_GAME_ON_STARTUP=true
CUSTOM_INSTRUCTIONS="Your custom prompt instructions ..."
COSMOS_MONGO_URI=your-cosmos-mongo-uri
```

## Usage

### Running the Scheduler

To start the Drawi Agent scheduler which handles game creation and closure tasks:
```bash
python src/drawi/run_scheduler.py
```

You can also specify custom intervals via command-line arguments:
```bash
python src/drawi/run_scheduler.py --game-interval 180
```

### Running Individual Modules

For testing or debugging, you may run modules separately:
- **Game Agent:** `python src/drawi/game_agent.py`
- **Scheduler:** `python src/drawi/run_scheduler.py`

## How to Customize

- **Game Logic:** Adjust prompts, timings, and winner selection in [src/drawi/game_agent.py](./src/drawi/game_agent.py).
- **Database Operations:** Modify game document structure in [src/drawi/game_store.py](./src/drawi/game_store.py).
- **API Tools:** Extend or alter functions in [src/drawi/tools.py](./src/drawi/tools.py) to integrate additional features.
- **Scheduler Behavior:** Customize task intervals or add new tasks in [src/drawi/scheduler.py](./src/drawi/scheduler.py).
- **Language Model:** Switch to a different language model by updating the configuration in [src/drawi/configuration.py](./src/drawi/configuration.py).

## Advanced Topics

- **Scaling and Deployment:** Drawi Agent can be containerized using Docker and deployed on cloud platforms such as Azure or AWS. Ensure all environment variables are securely managed.
- **Monitoring and Logging:** Integrate with centralized logging and monitoring solutions (e.g., ELK stack, Azure Monitor) for production environments.
- **Extending the ReAct Loop:** The LLM-based decision system can be tailored to different contest rules by modifying the prompt schema in the agent module.
- **Security Considerations:** Secure API keys and sensitive information by using secret management tools and following best practices.

## Troubleshooting

- **Missing Environment Variables:** Ensure your `.env` file is correctly set up; check logs for error messages.
- **Scheduler Issues:** Verify that APScheduler is running without conflicts; inspect job logs for misfire errors.
- **API Failures:** Check the validity of your API tokens and network connectivity to external services.
- **Database Connectivity:** Confirm that the Cosmos DB connection string (`COSMOS_MONGO_URI`) is accurate and that your IP is whitelisted if needed.

## Contributing

We welcome contributions to improve Drawi Agent. To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Ensure your code follows existing style guidelines.
4. Submit a pull request with a detailed description of your changes.
5. Include tests for new functionality where applicable.

## License

Drawi Agent is released under the MIT License. See [LICENSE](./LICENSE) for details.

Happy coding with Drawi Agent!
