"""
Twitter API Client (Updated)

This module provides a client for interacting with the Twitter API using the tweepy library.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

import tweepy

class TwitterClient:
    """Client for the Twitter API"""
    
    def __init__(self, api_key: str, api_secret: str, 
                 access_token: str, access_token_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.client_v1 = None
        self.client_v2 = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the Twitter client"""
        try:
            # Initialize both v1.1 and v2 clients for different functionalities
            # v1.1 for some legacy features, v2 for modern features
            auth = tweepy.OAuth1UserHandler(
                self.api_key, 
                self.api_secret,
                self.access_token, 
                self.access_token_secret
            )
            self.client_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            # v2 client for better functionality
            self.client_v2 = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Test authentication
            user = self.client_v2.get_me()
            if user.data:
                logging.info(f"Successfully authenticated as @{user.data.username}")
                self.initialized = True
                return True
            else:
                logging.error("Authentication failed - no user data returned")
                self.initialized = False
                return False
                
        except Exception as e:
            logging.error(f"Failed to initialize Twitter client: {str(e)}")
            self.initialized = False
            return False
    
    async def post_tweet(self, text: str) -> Dict[str, Any]:
        """Post a single tweet"""
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return {"success": False, "error": "Failed to initialize Twitter client"}
        
        try:
            
            # Real implementation using tweepy v2
            response = self.client_v2.create_tweet(text=text)
            
            if response.data:
                result = {
                    "id": response.data["id"],
                    "text": text,
                    "created_at": datetime.now().isoformat(),
                    "success": True
                }
                
                logging.info(f"Successfully posted tweet: {text[:50]}...")
                return result
            else:
                return {"success": False, "error": "No response data returned"}
            
        except Exception as e:
            logging.error(f"Failed to post tweet: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def search_tweets(self, query: str, count: int = 10) -> Dict[str, Any]:
        """Search for tweets"""
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return {"success": False, "error": "Failed to initialize Twitter client"}
        
        try:
            
            # Real implementation using tweepy v2
            tweets = tweepy.Paginator(
                self.client_v2.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'author_id', 'public_metrics'],
                user_fields=['username', 'name'],
                expansions=['author_id'],
                max_results=min(count, 100)  # API limit
            ).flatten(limit=count)
            
            tweet_list = []
            users_dict = {}
            
            # Process tweets and users
            for tweet in tweets:
                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else "unknown",
                    "author_id": tweet.author_id
                }
                tweet_list.append(tweet_data)
            
            # Get user information from includes
            if hasattr(tweets, 'includes') and 'users' in tweets.includes:
                for user in tweets.includes['users']:
                    users_dict[user.id] = {
                        "username": user.username,
                        "name": user.name
                    }
            
            result = {
                "tweets": tweet_list,
                "users": users_dict,
                "success": True
            }
            
            logging.info(f"Search for '{query}' returned {len(tweet_list)} tweets")
            return result
            
        except Exception as e:
            logging.error(f"Failed to search tweets: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Post a thread of tweets"""
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return {"success": False, "error": "Failed to initialize Twitter client"}
        
        try:
            # Real implementation using tweepy v2
            posted_tweets = []
            reply_to_id = None
            
            for i, tweet_text in enumerate(tweets):
                try:
                    if reply_to_id:
                        # This is a reply to the previous tweet in the thread
                        response = self.client_v2.create_tweet(
                            text=tweet_text,
                            in_reply_to_tweet_id=reply_to_id
                        )
                    else:
                        # This is the first tweet in the thread
                        response = self.client_v2.create_tweet(text=tweet_text)
                    
                    if response.data:
                        tweet_data = {
                            "id": response.data["id"],
                            "text": tweet_text,
                            "created_at": datetime.now().isoformat(),
                            "in_reply_to_tweet_id": reply_to_id
                        }
                        posted_tweets.append(tweet_data)
                        reply_to_id = response.data["id"]  # Next tweet will reply to this one
                    else:
                        logging.error(f"Failed to post tweet {i+1} in thread")
                        break
                        
                except Exception as e:
                    logging.error(f"Error posting tweet {i+1} in thread: {str(e)}")
                    break
            
            if posted_tweets:
                result = {
                    "tweets": posted_tweets,
                    "success": True
                }
                logging.info(f"Successfully posted thread with {len(posted_tweets)} tweets")
                return result
            else:
                return {"success": False, "error": "No tweets were posted successfully"}
            
        except Exception as e:
            logging.error(f"Failed to post thread: {str(e)}")
            return {"success": False, "error": str(e)}