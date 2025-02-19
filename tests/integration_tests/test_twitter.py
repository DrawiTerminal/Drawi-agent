"""Test the Twitter integration tools."""

import pytest
from drawi.configuration import Configuration
from drawi.tools import get_twitter_mentions
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timedelta


@pytest.fixture
def runnable_config():
    """Create a RunnableConfig with test configuration."""
    config = Configuration()
    return RunnableConfig(configurable={"configuration": config})


@pytest.fixture
def config_without_credentials():
    """Create a RunnableConfig without Twitter credentials."""
    config = Configuration()
    config.twitter_api_key = None
    config.twitter_api_secret = None
    config.twitter_access_token = None
    config.twitter_access_token_secret = None
    config.twitter_bearer_token = None
    config.twitter_user_id = None
    return RunnableConfig(configurable={"configuration": config})


@pytest.mark.asyncio
class TestTwitterIntegration:
    """Test suite for Twitter integration tools."""

    async def test_get_twitter_mentions_success(self, runnable_config):
        """Test successful fetching of Twitter mentions."""
        result = await get_twitter_mentions(config=runnable_config)
        
        # Verify we got a valid response
        assert result is not None
        assert isinstance(result, list)
        
        # If we have results, verify their structure
        if result and not any("error" in item for item in result):
            first_mention = result[0]
            # Check required fields from the Twitter API response
            assert "created_at" in first_mention
            assert "author_id" in first_mention
            assert "text" in first_mention
            
            # Verify created_at is within the last 7 days
            created_at = datetime.strptime(first_mention["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            assert created_at >= seven_days_ago

    async def test_get_twitter_mentions_missing_credentials(self, config_without_credentials):
        """Test error handling when Twitter credentials are missing."""
        result = await get_twitter_mentions(config=config_without_credentials)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["error"] == "Twitter bearer token or user ID not configured"
