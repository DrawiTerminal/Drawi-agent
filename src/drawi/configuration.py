"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import os
from typing import Annotated, Optional, List

from langchain_core.runnables import RunnableConfig, ensure_config

from drawi import prompts


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    system_prompt: str = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="azure/gpt-4o",  # Changed default to use Azure OpenAI
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    max_tweets_to_process: int = field(
        default=20,
        metadata={
            "description": "Maximum number of tweets to process before stopping"
        },
    )

    min_engagement_rate: float = field(
        default=0.01,
        metadata={
            "description": "Minimum engagement rate (likes + retweets / followers) for user quality assessment"
        },
    )

    twitter_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("X_API_KEY"),
        metadata={
            "description": "Twitter API Key (Consumer Key) for OAuth authentication"
        },
    )

    twitter_api_secret: Optional[str] = field(
        default_factory=lambda: os.getenv("X_API_SECRET"),
        metadata={
            "description": "Twitter API Secret (Consumer Secret) for OAuth authentication"
        },
    )

    twitter_access_token: Optional[str] = field(
        default_factory=lambda: os.getenv("X_ACCESS_TOKEN"),
        metadata={
            "description": "Twitter Access Token for OAuth authentication"
        },
    )

    twitter_access_token_secret: Optional[str] = field(
        default_factory=lambda: os.getenv("X_ACCESS_TOKEN_SECRET"),
        metadata={
            "description": "Twitter Access Token Secret for OAuth authentication"
        },
    )

    twitter_bearer_token: Optional[str] = field(
        default_factory=lambda: os.getenv("X_BEARER_TOKEN"),
        metadata={
            "description": "Twitter API Bearer Token for App-only authentication"
        },
    )

    twitter_user_id: Optional[str] = field(
        default_factory=lambda: os.getenv("X_USER_ID"),
        metadata={
            "description": "Twitter User ID to fetch mentions for"
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        if isinstance(config, cls):
            return config
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
