#!/usr/bin/env python3
"""
Bluesky MCP Server - Python Implementation (Updated)

This server provides a Python implementation of the Bluesky MCP server
with support for the create-post functionality using the modern MCP Python SDK.
"""

import os
import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from bluesky_api import BlueskyAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("bluesky-mcp")

# Load environment variables
BLUESKY_IDENTIFIER = os.environ.get("BLUESKY_IDENTIFIER")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD")
BLUESKY_SERVICE_URL = os.environ.get("BLUESKY_SERVICE_URL", "https://bsky.social")
LOG_RESPONSES = os.environ.get("LOG_RESPONSES", "false").lower() == "true"

# Initialize FastMCP server
mcp = FastMCP("bluesky")

# Initialize Bluesky client
bluesky_client = None

def get_bluesky_client() -> BlueskyAPI:
    """Get or create Bluesky client singleton"""
    global bluesky_client
    if bluesky_client is None:
        if not BLUESKY_IDENTIFIER or not BLUESKY_APP_PASSWORD:
            logger.warning("BLUESKY_IDENTIFIER or BLUESKY_APP_PASSWORD not set, using mock mode")
            # Use placeholder values in mock mode
            identifier = BLUESKY_IDENTIFIER or "user.bsky.social"
            password = BLUESKY_APP_PASSWORD or "password"
        else:
            identifier = BLUESKY_IDENTIFIER
            password = BLUESKY_APP_PASSWORD
            
        bluesky_client = BlueskyAPI(
            identifier,
            password,
            BLUESKY_SERVICE_URL
        )
    return bluesky_client

@mcp.tool()
async def create_post(text: str, reply_to: Optional[str] = None) -> str:
    """
    Create a new post on Bluesky
    
    Args:
        text: The content of your post (max 300 characters)
        reply_to: Optional URI of post to reply to
        
    Returns:
        Success message with post URI
    """
    try:
        if len(text) > 300:
            return "Error: Post text cannot exceed 300 characters"
            
        client = get_bluesky_client()
        
        # Ensure client is logged in
        if not client.logged_in:
            success = await client.login()
            if not success:
                return "Error: Failed to login to Bluesky"
        
        result = await client.create_post(text, reply_to)
        
        if LOG_RESPONSES:
            logger.info(f"Post result: {result}")
        
        if result.get("success", False):
            post_uri = result.get("uri", "unknown")
            return f"Successfully created post! URI: {post_uri}"
        else:
            error_msg = result.get("error", "Unknown error")
            return f"Failed to create post: {error_msg}"
            
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        return f"Error creating post: {str(e)}"

async def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting Bluesky MCP server...")
        
        # Initialize Bluesky client on startup
        try:
            client = get_bluesky_client()
            await client.login()
            logger.info("Successfully initialized Bluesky client")
        except Exception as e:
            logger.warning(f"Could not initialize Bluesky client: {str(e)} - will attempt on first request")
        
        # Run the server with stdio transport (for fast-agent compatibility)
        await mcp.run(transport="stdio")
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
