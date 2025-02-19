"""This module provides tools for web search and social media interactions."""

from typing import Any, Callable, List, Optional, Dict, cast
from datetime import datetime, timedelta
import tweepy

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, Tool
from typing_extensions import Annotated

from drawi.configuration import Configuration

async def get_twitter_mentions(
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Fetch recent Twitter mentions for the configured user.
    
    Args:
        config (RunnableConfig): Configuration containing Twitter credentials and user ID
    
    Returns:
        Optional[list[dict[str, Any]]]: List of mention objects with tweet details,
            or a list containing an error message if the request fails
    """
    configuration = Configuration.from_runnable_config(config)
    
    if not configuration.twitter_bearer_token or not configuration.twitter_user_id:
        return [{"error": "Twitter bearer token or user ID not configured"}]
    
    try:
        client = tweepy.Client(bearer_token=configuration.twitter_bearer_token)
        
        # Get mentions from the last 7 days
        start_time = datetime.utcnow() - timedelta(days=7)
        
        response = client.get_users_mentions(
            id=configuration.twitter_user_id,
            start_time=start_time,
            tweet_fields=["created_at", "author_id", "text", "public_metrics"],
            max_results=configuration.max_tweets_to_process
        )
        
        if not response.data:
            return []
        
        processed_tweets = []
        for tweet in response.data:
            # Get author info for filtering
            author_info = await get_user_info(tweet.author_id, config=config)
            if isinstance(author_info, dict) and "error" not in author_info:
                # Calculate engagement rate
                metrics = author_info["metrics"]
                followers = metrics["followers_count"]
                engagement_rate = 0.0
                if followers > 0 and "public_metrics" in tweet.data:
                    tweet_metrics = tweet.data["public_metrics"]
                    total_engagement = tweet_metrics.get("like_count", 0) + tweet_metrics.get("retweet_count", 0)
                    engagement_rate = total_engagement / followers

                # Calculate account age
                created_at = datetime.fromisoformat(author_info["created_at"].replace("Z", "+00:00"))
                account_age_days = (datetime.utcnow() - created_at).days

                # Add filtering metrics to tweet data
                tweet_data = tweet.data
                tweet_data["author"] = {
                    "followers_count": followers,
                    "account_age_days": account_age_days,
                    "engagement_rate": engagement_rate
                }
                processed_tweets.append(tweet_data)

        return processed_tweets
        
    except tweepy.TweepyException as e:
        return [{"error": f"Twitter API error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Failed to fetch Twitter mentions: {str(e)}"}]

async def search(
    query: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Search for general web results using Tavily."""
    configuration = Configuration.from_runnable_config(config)
    wrapped = TavilySearchResults(max_results=configuration.max_search_results)
    result = await wrapped.ainvoke({"query": query})
    return cast(list[dict[str, Any]], result)

async def reply_to_tweet(
    tweet_id: str,
    text: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Reply to a specific tweet with given text.
    
    Args:
        tweet_id (str): The ID of the tweet to reply to
        text (str): The text content of the reply
        config (RunnableConfig): Configuration containing Twitter credentials
    
    Returns:
        Optional[dict[str, Any]]: Dictionary with reply details or error message
    """
    configuration = Configuration.from_runnable_config(config)
    
    if not all([
        configuration.twitter_api_key,
        configuration.twitter_api_secret,
        configuration.twitter_access_token,
        configuration.twitter_access_token_secret
    ]):
        return {"error": "Twitter OAuth credentials not configured"}
    
    try:
        client = tweepy.Client(
            consumer_key=configuration.twitter_api_key,
            consumer_secret=configuration.twitter_api_secret,
            access_token=configuration.twitter_access_token,
            access_token_secret=configuration.twitter_access_token_secret
        )
        
        # Post the reply
        response = client.create_tweet(
            text=text,
            in_reply_to_tweet_id=tweet_id
        )
        
        if response.data:
            tweet_data = response.data
            return {
                "id": tweet_data["id"],
                "text": tweet_data["text"],
                "status": "success"
            }
        return {"error": "Failed to post reply"}
            
    except tweepy.TweepyException as e:
        return {"error": f"Twitter API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to reply to tweet: {str(e)}"}

async def get_user_info(
    user_id: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Fetch detailed information about a Twitter user by their user ID.
    
    Args:
        user_id (str): The Twitter user ID
        config (RunnableConfig): Configuration containing Twitter credentials
    
    Returns:
        Optional[dict[str, Any]]: Dictionary containing user information or error message
    """
    configuration = Configuration.from_runnable_config(config)
    
    if not configuration.twitter_bearer_token:
        return {"error": "Twitter bearer token not configured"}
    
    try:
        client = tweepy.Client(bearer_token=configuration.twitter_bearer_token)
        
        # Get user information
        response = client.get_user(
            id=user_id,
            user_fields=[
                "created_at",
                "description",
                "location",
                "profile_image_url",
                "protected",
                "public_metrics",
                "url",
                "verified"
            ]
        )
        
        if not response.data:
            return {"error": f"User with ID {user_id} not found"}
            
        user = response.data
        
        # Extract public metrics
        metrics = user.public_metrics
        followers = metrics["followers_count"]
        
        return {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "description": user.description,
            "location": user.location,
            "url": user.url,
            "profile_image_url": user.profile_image_url,
            "protected": user.protected,
            "verified": user.verified,
            "created_at": user.created_at,
            "followers": followers,  # Direct follower count field
            "metrics": {  # Detailed metrics in a separate object
                "followers_count": followers,
                "following_count": metrics["following_count"],
                "tweet_count": metrics["tweet_count"],
                "listed_count": metrics["listed_count"]
            }
        }
        
    except tweepy.TweepyException as e:
        return {"error": f"Twitter API error: {str(e)}"} 
    except Exception as e:
        return {"error": f"Failed to fetch user info: {str(e)}"}

async def get_tweet(
    tweet_identifier: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Fetch tweet content and data based on tweet ID or URL.
    
    Args:
        tweet_identifier (str): Tweet ID or URL
        config (RunnableConfig): Configuration containing Twitter credentials
    
    Returns:
        Optional[dict[str, Any]]: Dictionary containing tweet data or error message
    """
    configuration = Configuration.from_runnable_config(config)
    
    if not configuration.twitter_bearer_token:
        return {"error": "Twitter bearer token not configured"}
    
    try:
        # Extract tweet ID from URL if URL is provided
        tweet_id = tweet_identifier
        if "twitter.com" in tweet_identifier or "x.com" in tweet_identifier:
            # Extract ID from URL formats like:
            # https://twitter.com/username/status/1234567890
            # https://x.com/username/status/1234567890
            tweet_id = tweet_identifier.split("/status/")[-1].split("?")[0]
        
        client = tweepy.Client(bearer_token=configuration.twitter_bearer_token)
        
        # Get tweet information with expansions and fields
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=[
                "created_at",
                "author_id",
                "conversation_id",
                "public_metrics",
                "entities",
                "referenced_tweets"
            ],
            expansions=["author_id", "referenced_tweets.id"],
            user_fields=[
                "name",
                "username",
                "profile_image_url",
                "verified"
            ]
        )
        
        if not response.data:
            return {"error": f"Tweet with ID {tweet_id} not found"}
            
        tweet = response.data
        
        # Get author info from includes
        author = None
        if response.includes and "users" in response.includes:
            author = response.includes["users"][0].data
        
        # Process referenced tweets if any
        referenced_tweets = []
        if response.includes and "tweets" in response.includes:
            referenced_tweets = [ref_tweet.data for ref_tweet in response.includes["tweets"]]
        
        return {
            "id": tweet.id,
            "text": tweet.text,
            "created_at": tweet.created_at,
            "author": {
                "id": author["id"] if author else tweet.author_id,
                "name": author["name"] if author else None,
                "username": author["username"] if author else None,
                "profile_image_url": author["profile_image_url"] if author else None,
                "verified": author["verified"] if author else None
            },
            "metrics": tweet.public_metrics,
            "conversation_id": tweet.conversation_id,
            "entities": tweet.entities,
            "referenced_tweets": [
                {
                    "type": ref["type"],
                    "id": ref["id"]
                } for ref in (tweet.referenced_tweets or [])
            ],
            "referenced_tweets_content": referenced_tweets
        }
        
    except tweepy.TweepyException as e:
        return {"error": f"Twitter API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch tweet: {str(e)}"} 

# New function: find_answers retrieves all replies using the conversation_id endpoint.
async def find_answers_with_conversation_id(
    tweet_id: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve all tweets that are in reply to the given tweet_id using the conversation_id endpoint.
    
    Args:
        tweet_id (str): The ID of the tweet for which replies are fetched.
        config: RunnableConfig containing Twitter credentials.

    Returns:
        Optional[List[Dict[str, Any]]]: List of reply tweets or an error message.
    """
    configuration = Configuration.from_runnable_config(config)
    if not configuration.twitter_bearer_token:
        return [{"error": "Twitter bearer token not configured"}]
    try:
        client = tweepy.Client(bearer_token=configuration.twitter_bearer_token)
       
        query = f"conversation_id:{tweet_id}"
        response = client.search_recent_tweets(
            query=query,
            tweet_fields=["created_at", "author_id", "text", "in_reply_to_user_id"],
            user_fields=[
                "name",
                "username",
                "profile_image_url",
                "verified"
            ],
            expansions=["author_id"],   # Added expansion to fetch user details
            max_results=50
        )
        
        if not response.data:
            return []
        
        # Map users from the includes if available
        user_map = {}
        if response.includes and "users" in response.includes:
            for user in response.includes["users"]:
                user_map[user.id] = user.data
        
        replies = []
        for tweet in response.data:
            if tweet.id == tweet_id:
                continue
            tweet_data = tweet.data
            author_info = user_map.get(tweet.author_id)
            if author_info:
                tweet_data["author"] = {
                    "username": author_info.get("username"),
                    "profile_image_url": author_info.get("profile_image_url"),
                    "verified": author_info.get("verified"),
                    "name": author_info.get("name")
                }
            replies.append(tweet_data)
        return replies
    except tweepy.TweepyException as e:
        return [{"error": f"Twitter API error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Failed to fetch replies: {str(e)}"}]

async def search_tweets(
    keywords: List[str],
    limit: int = 20,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
   
    """Search for popular tweets containing specific keywords.
    
    Args:
        keywords (List[str]): List of keywords to search for
        limit (int, optional): Maximum number of tweets to return. Defaults to 20.
        config (RunnableConfig): Configuration containing Twitter credentials
    
    Returns:
        Optional[list[dict[str, Any]]]: List of tweet objects sorted by popularity,
            or a list containing an error message if the request fails
    """
    return []
    configuration = Configuration.from_runnable_config(config)
    
    if not configuration.twitter_bearer_token:
        return [{"error": "Twitter bearer token not configured"}]
    
    try:
        client = tweepy.Client(bearer_token=configuration.twitter_bearer_token)
        
        # Construct query string from keywords
        query = " ".join(keywords)
        
        # Search for tweets with the specified query
        response = client.search_recent_tweets(
            query=query,
            max_results=min(limit, 100),  # API limit is 100
            tweet_fields=["created_at", "author_id", "public_metrics"],
            sort_order="relevancy"  # Get most relevant/popular tweets
        )
        
        if not response.data:
            return []
        
        # Process tweets and sort by popularity
        processed_tweets = []
        for tweet in response.data:
            metrics = tweet.public_metrics
            popularity_score = (
                metrics.get("like_count", 0) * 2 +  # Likes weighted more
                metrics.get("retweet_count", 0) * 3 +  # Retweets weighted most
                metrics.get("reply_count", 0)  # Replies weighted least
            )
            
            processed_tweets.append({
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "author_id": tweet.author_id,
                "metrics": metrics,
                "popularity_score": popularity_score
            })
        
        # Sort by popularity score and limit results
        processed_tweets.sort(key=lambda x: x["popularity_score"], reverse=True)
        return processed_tweets[:limit]
        
    except tweepy.TweepyException as e:
        return [{"error": f"Twitter API error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Failed to search tweets: {str(e)}"}]

async def post_tweet(
    text: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Post a new tweet with the given text.
    
    Args:
        text (str): The text content of the tweet
        config (RunnableConfig): Configuration containing Twitter credentials
    
    Returns:
        Optional[dict[str, Any]]: Dictionary with tweet details or error message
    """
    configuration = Configuration.from_runnable_config(config)
    
    if not all([
        configuration.twitter_api_key,
        configuration.twitter_api_secret,
        configuration.twitter_access_token,
        configuration.twitter_access_token_secret,
        configuration.twitter_bearer_token
    ]):
        return {"error": "Twitter OAuth credentials not configured"}
    
    try:
        client = tweepy.Client(
            consumer_key=configuration.twitter_api_key,
            consumer_secret=configuration.twitter_api_secret,
            access_token=configuration.twitter_access_token,
            access_token_secret=configuration.twitter_access_token_secret,
            bearer_token=configuration.twitter_bearer_token
        )
        
        # Post the tweet
        response = client.create_tweet(text=text)
        
        if response.data:
            tweet_data = response.data
            return {
                "id": tweet_data["id"],
                "text": tweet_data["text"],
                "status": "success"
            }
        return {"error": "Failed to post tweet"}
            
    except tweepy.TweepyException as e:
        return {"error": f"Twitter API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to post tweet: {str(e)}"}

######### MOCK IMPLEMENTATIONS #########
async def search_tweets_mock(
    keywords: list[str],
    limit: int = 20,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> list[dict[str, any]]:
    """Return a set of fake tweets simulating search results for a joke game.
    
    Args:
        keywords: List of keywords for the game query.
        limit: Maximum number of fake tweets to return.
        config: RunnableConfig (unused in mock).
    
    Returns:
        List of fake tweet dictionaries.
    """
    from datetime import datetime
    import random, string
    
    def generate_wallet() -> str:
        # Generate a valid Solana wallet address that starts with "So" and has 42 characters in total.
        return "So" + "".join(random.choices(string.ascii_letters + string.digits, k=40))
    
    # List of sample jokes for a more realistic tweet
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "I told my computer I needed a break, and it replied 'Restart me, please.'",
        "Why did the programmer quit his job? He didn't get arrays.",
        "I asked my phone why it was acting up; it said 'It's your fault, code buggy!'",
        "Debugging: Removing the needles from the haystack of bugs."
    ]
    
    fake_tweets = []
    num_tweets = min(limit, 5)  # generate up to 5 fake tweets
    for i in range(num_tweets):
        wallet = generate_wallet()
        joke = random.choice(jokes)
        # Construct a realistic tweet text based on the joke game
        tweet_text = f"{joke} #BestJokeChallenge Wallet: {wallet}"
        tweet = {
            "id": f"fake_{i}",
            "text": tweet_text,
            "created_at": datetime.utcnow().isoformat(),
            "author_id": f"author_{i}",
            "metrics": {
                "like_count": random.randint(0, 100),
                "retweet_count": random.randint(0, 50),
                "reply_count": random.randint(0, 20)
            }
        }
        tweet["popularity_score"] = (
            tweet["metrics"]["like_count"] * 2 +
            tweet["metrics"]["retweet_count"] * 3 +
            tweet["metrics"]["reply_count"]
        )
        fake_tweets.append(tweet)
    return fake_tweets

async def post_tweet_mock(
    text: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Post a new tweet with the given text.
    
    Args:
        text (str): The text content of the tweet
        config (RunnableConfig): Configuration containing Twitter credentials
    
    Returns:
        Optional[dict[str, Any]]: Dictionary with tweet details or error message
    """
    return {
        "id": "fake_tweet_id",
        "text": text,
        "status": "success"
    }

async def post_tweet_reply_mock(
    tweet_id: str,
    text: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Simulate posting a tweet reply for the winner announcement.
    
    Args:
        tweet_id (str): The ID of the tweet to reply to.
        text (str): The reply text.
        config (RunnableConfig): Configuration object (unused in mock).
    
    Returns:
        Optional[dict[str, Any]]: A mock tweet reply object.
    """
    return {
        "id": f"reply_to_{tweet_id}",
        "text": text,
        "in_reply_to_tweet_id": tweet_id,
        "status": "success"
    }

TOOLS: List[Callable[..., Any]] = [
    search,
    get_twitter_mentions,
    reply_to_tweet,
    get_user_info,
    post_tweet,
    get_tweet,
    search_tweets,
    find_answers_with_conversation_id
]
