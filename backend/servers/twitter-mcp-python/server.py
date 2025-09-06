#!/usr/bin/env python3
"""
Twitter MCP Server - Python Implementation (Updated)

This server provides a Python implementation of the Twitter MCP server
with support for posting tweets, searching tweets, and posting threads 
using the modern MCP Python SDK.
"""

import os
import asyncio
import logging
import uuid
from typing import Optional, List
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from twitter_api import TwitterClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("twitter-mcp")

# Load environment variables
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET_KEY = os.environ.get("TWITTER_API_SECRET_KEY")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

# Mock mode is enabled if credentials are missing
MOCK_MODE = not (TWITTER_API_KEY and TWITTER_API_SECRET_KEY and 
                 TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_TOKEN_SECRET)

if MOCK_MODE:
    logger.warning("Twitter API credentials not set. Running in mock mode.")

# Initialize FastMCP server
mcp = FastMCP("twitter")

# Initialize Twitter client
twitter_client = None

def get_twitter_client() -> TwitterClient:
    """Get or create Twitter client singleton"""
    global twitter_client
    if twitter_client is None:
        api_key = TWITTER_API_KEY or "mock_api_key"
        api_secret = TWITTER_API_SECRET_KEY or "mock_api_secret"
        access_token = TWITTER_ACCESS_TOKEN or "mock_access_token"
        access_token_secret = TWITTER_ACCESS_TOKEN_SECRET or "mock_access_token_secret"
        
        twitter_client = TwitterClient(
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
    return twitter_client

@mcp.tool()
async def post_tweet(text: str) -> str:
    """
    Post a new tweet to Twitter
    
    Args:
        text: The content of your tweet (max 280 characters)
        
    Returns:
        Success message with tweet URL
    """
    try:
        if len(text) > 280:
            return f"Error: Tweet exceeds 280 characters (has {len(text)})"
            
        client = get_twitter_client()
        
        # Ensure client is initialized
        if not client.initialized:
            success = await client.initialize()
            if not success:
                return "Error: Failed to initialize Twitter client"
        
        result = await client.post_tweet(text)
        
        if result.get("success", False):
            tweet_id = result.get("id", "unknown")
            return f"Successfully posted tweet! URL: https://twitter.com/status/{tweet_id}"
        else:
            error_msg = result.get("error", "Unknown error")
            return f"Failed to post tweet: {error_msg}"
            
    except Exception as e:
        logger.error(f"Error posting tweet: {str(e)}")
        return f"Error posting tweet: {str(e)}"

@mcp.tool()
async def search_tweets(query: str, count: int = 10) -> str:
    """
    Search for tweets on Twitter
    
    Args:
        query: Search query
        count: Number of tweets to return (10-100, default: 10)
        
    Returns:
        Formatted search results
    """
    try:
        if count < 10 or count > 100:
            return "Error: Count must be between 10 and 100"
            
        client = get_twitter_client()
        
        # Ensure client is initialized
        if not client.initialized:
            success = await client.initialize()
            if not success:
                return "Error: Failed to initialize Twitter client"
        
        result = await client.search_tweets(query, count)
        
        if result.get("success", False):
            tweets = result.get("tweets", [])
            users = result.get("users", {})
            
            if not tweets:
                return f"No tweets found for query: '{query}'"
            
            formatted_results = [f"Search results for '{query}' ({len(tweets)} tweets):\n"]
            
            for i, tweet in enumerate(tweets, 1):
                user_id = tweet.get("author_id", "unknown")
                user_info = users.get(user_id, {})
                username = user_info.get("username", "unknown")
                name = user_info.get("name", "Unknown User")
                
                formatted_results.append(f"{i}. @{username} ({name})")
                formatted_results.append(f"   {tweet.get('text', '')}")
                formatted_results.append(f"   Created: {tweet.get('created_at', 'unknown')}")
                formatted_results.append(f"   URL: https://twitter.com/{username}/status/{tweet.get('id', '')}")
                formatted_results.append("")
            
            return "\n".join(formatted_results)
        else:
            error_msg = result.get("error", "Unknown error")
            return f"Failed to search tweets: {error_msg}"
            
    except Exception as e:
        logger.error(f"Error searching tweets: {str(e)}")
        return f"Error searching tweets: {str(e)}"

@mcp.tool()
async def post_thread(tweets: List[str]) -> str:
    """
    Post a thread of tweets to Twitter
    
    Args:
        tweets: Array of tweet contents for the thread (each max 280 characters)
        
    Returns:
        Success message with thread details
    """
    try:
        if not tweets:
            return "Error: Thread must contain at least one tweet"
            
        if len(tweets) > 25:  # Twitter's thread limit
            return "Error: Thread cannot exceed 25 tweets"
            
        # Validate each tweet length
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                return f"Error: Tweet {i+1} exceeds 280 characters (has {len(tweet)})"
                
        client = get_twitter_client()
        
        # Ensure client is initialized
        if not client.initialized:
            success = await client.initialize()
            if not success:
                return "Error: Failed to initialize Twitter client"
        
        result = await client.post_thread(tweets)
        
        if result.get("success", False):
            thread_tweets = result.get("tweets", [])
            if thread_tweets:
                first_tweet_id = thread_tweets[0].get("id", "unknown")
                return f"Successfully posted thread with {len(thread_tweets)} tweets! First tweet: https://twitter.com/status/{first_tweet_id}"
            else:
                return "Thread posted successfully!"
        else:
            error_msg = result.get("error", "Unknown error")
            return f"Failed to post thread: {error_msg}"
            
    except Exception as e:
        logger.error(f"Error posting thread: {str(e)}")
        return f"Error posting thread: {str(e)}"

async def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting Twitter MCP server...")
        
        # Initialize Twitter client on startup
        try:
            client = get_twitter_client()
            await client.initialize()
            mode = "mock" if MOCK_MODE else "live"
            logger.info(f"Successfully initialized Twitter client in {mode} mode")
        except Exception as e:
            logger.warning(f"Could not initialize Twitter client: {str(e)} - will attempt on first request")
        
        # Run the server with stdio transport (for fast-agent compatibility)
        await mcp.run(transport="stdio")
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
