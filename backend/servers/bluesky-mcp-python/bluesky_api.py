"""
Bluesky API Client (Updated)

This module provides a client for interacting with the Bluesky API using the atproto library.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from atproto import Client

class BlueskyAPI:
    """Client for the Bluesky API"""
    
    def __init__(self, identifier: str, password: str, service_url: str = "https://bsky.social"):
        self.identifier = identifier
        self.password = password
        self.service_url = service_url
        self.client = Client(base_url=service_url)
        self.logged_in = False
    
    async def login(self) -> bool:
        """Login to Bluesky"""
        try:
            # Real implementation using atproto
            profile = self.client.login(self.identifier, self.password)
            logging.info(f"Successfully logged in as {profile.handle} ({profile.did})")
            self.logged_in = True
            return True
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            self.logged_in = False
            return False
    
    async def create_post(self, text: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Create a post on Bluesky"""
        if not self.logged_in:
            success = await self.login()
            if not success:
                return {"success": False, "error": "Failed to login"}
        
        try:
            # Real implementation using atproto
            post_record = {
                "text": text,
                "createdAt": datetime.now().isoformat()
            }
            
            # Handle reply if specified
            if reply_to:
                try:
                    # Parse the reply URI and get the post to reply to
                    reply_thread = self.client.get_post_thread(reply_to)
                    if reply_thread and reply_thread.thread:
                        post_record["reply"] = {
                            "root": {
                                "uri": reply_to,
                                "cid": reply_thread.thread.post.cid
                            },
                            "parent": {
                                "uri": reply_to, 
                                "cid": reply_thread.thread.post.cid
                            }
                        }
                except Exception as e:
                    logging.warning(f"Could not set up reply: {str(e)}")
            
            # Create the post
            response = self.client.send_post(text=text, reply_to=reply_to if reply_to else None)
            
            result = {
                "uri": response.uri,
                "cid": response.cid,
                "success": True
            }
            
            logging.info(f"Successfully posted to Bluesky: {text[:50]}...")
            return result
            
        except Exception as e:
            logging.error(f"Failed to post: {str(e)}")
            return {"success": False, "error": str(e)}
