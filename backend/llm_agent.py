#!/usr/bin/env python
"""
LLM-Powered MCP Agent

This module creates an intelligent agent that can interact with our MCP servers
using natural language queries and automatically select appropriate tools.
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from openai import AsyncOpenAI


class MCPLLMAgent:
    """
    An intelligent agent that uses LLM to interact with MCP servers
    """
    
    def __init__(self, blackbox_api_key: Optional[str] = None, model: str = "blackboxai-pro"):
        """
        Initialize the MCP LLM Agent using BlackboxAI
        
        Args:
            blackbox_api_key: BlackboxAI API key (or use BLACKBOX_API_KEY env var)
            model: BlackboxAI model to use
        """

        self.api_key = blackbox_api_key or os.getenv("BLACKBOX_API_KEY")
        if not self.api_key:
            raise ValueError("BlackboxAI API key is required. Set BLACKBOX_API_KEY environment variable.")
            
        self.model = model
        self.base_url = "https://api.blackbox.ai/v1"
        self.app = None
        self.agents = {}
        self._setup_mcp_app()
    
    def _setup_mcp_app(self):
        """Setup MCP application with server configurations"""
        
        # MCP server configurations
        mcp_config = {
            "mcp": {
                "servers": {
                    "blackbox": {
                        "command": "uv",
                        "args": ["run", "python", "servers/bbai_mcp_server/blackbox_mcp_server/server.py"],
                        "env": dict(os.environ),
                        "cwd": str(Path(__file__).parent)
                    },
                    "bluesky": {
                        "command": "uv", 
                        "args": ["run", "python", "servers/bluesky-mcp-python/server.py"],
                        "env": dict(os.environ),
                        "cwd": str(Path(__file__).parent)
                    },
                    "linkedin": {
                        "command": "uv",
                        "args": ["run", "python", "servers/linkedin-mcp/linkedin_mcp/server.py"], 
                        "env": dict(os.environ),
                        "cwd": str(Path(__file__).parent)
                    },
                    "twitter": {
                        "command": "uv",
                        "args": ["run", "python", "servers/twitter-mcp-python/server.py"],
                        "env": dict(os.environ), 
                        "cwd": str(Path(__file__).parent)
                    }
                }
            }
        }
        
        # Initialize MCP app
        self.app = MCPApp(mcp_config)
        
        # Create specialized agents for different tasks
        self._create_agents()
    
    def _create_agents(self):
        """Create a single test agent"""
        
        # Set up the LLM client for agents using BlackboxAI
        llm_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Multi-Platform Agent (combines all capabilities)
        self.agents["multi_platform"] = Agent(
            name="multi_platform", 
            instruction="""You are an AI assistant with access to multiple tools and platforms. You can:
            - Generate content using AI tools (Blackbox)
            - Post and manage content on social media (Twitter, Bluesky, LinkedIn)
            - Search for information and trends
            - Create comprehensive content strategies
            
            Always choose the most appropriate tools for each task and explain your actions.""",
            server_names=["blackbox", "twitter", "bluesky", "linkedin"],
            model=self.model,
            llm=llm_client
        )
    
    async def chat(self, message: str, agent_name: str = "multi_platform") -> str:
        """
        Chat with a specific agent
        
        Args:
            message: User message/query
            agent_name: Which agent to use ("multi_platform")
            
        Returns:
            Agent's response
        """
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}")
        
        if not self.app:
            raise RuntimeError("MCP app not initialized")
        
        try:
            # Run the agent with the user message
            async with self.app.run() as run:
                agent = self.agents[agent_name]
                response = await agent.generate_str(message)
                return response
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def generate_content(self, topic: str, platform: str = "general") -> str:
        """
        Generate content for a specific topic and platform
        
        Args:
            topic: Content topic or description
            platform: Target platform ("twitter", "bluesky", "linkedin", "general")
            
        Returns:
            Generated content
        """
        platform_instructions = {
            "twitter": "Create a concise, engaging tweet (max 280 characters) with relevant hashtags",
            "bluesky": "Create an engaging post for Bluesky with a conversational tone", 
            "linkedin": "Create a professional LinkedIn post with business insights",
            "general": "Create engaging content suitable for multiple platforms"
        }
        
        instruction = platform_instructions.get(platform, platform_instructions["general"])
        prompt = f"{instruction} about: {topic}"
        
        return await self.chat(prompt, "multi_platform")
    
    async def post_to_platform(self, content: str, platform: str) -> str:
        """
        Post content to a specific social media platform
        
        Args:
            content: Content to post
            platform: Target platform ("twitter", "bluesky", "linkedin")
            
        Returns:
            Result of posting attempt
        """
        platform_prompts = {
            "twitter": f"Post this tweet to Twitter: {content}",
            "bluesky": f"Create a post on Bluesky with this content: {content}",
            "linkedin": f"Post this to LinkedIn: {content}"
        }
        
        if platform not in platform_prompts:
            return f"Unsupported platform: {platform}"
        
        prompt = platform_prompts[platform]
        return await self.chat(prompt, "multi_platform")
    
    async def search_content(self, query: str, platform: str = "twitter") -> str:
        """
        Search for content on social media platforms
        
        Args:
            query: Search query
            platform: Platform to search on
            
        Returns:
            Search results
        """
        prompt = f"Search for '{query}' on {platform} and provide a summary of relevant posts"
        return await self.chat(prompt, "multi_platform")
    
    def list_agents(self) -> List[str]:
        """List available agents"""
        return list(self.agents.keys())
    
    def get_agent_description(self, agent_name: str) -> str:
        """Get description of a specific agent"""
        if agent_name not in self.agents:
            return f"Unknown agent: {agent_name}"
        
        agent = self.agents[agent_name]
        return f"Agent '{agent_name}': {agent.instruction}"


# CLI Interface for testing the agent
async def main():
    """Interactive CLI for testing the MCP LLM Agent"""
    
    try:
        # Initialize the agent
        print("🚀 Initializing MCP LLM Agent...")
        agent = MCPLLMAgent()
        
        print("✅ Agent initialized successfully!")
        print(f"Available agents: {', '.join(agent.list_agents())}")
        print("\nType 'help' for commands, 'quit' to exit")
        
        while True:
            try:
                # Get user input
                user_input = input("\n🤖 Ask the agent: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                
                if user_input.lower() == "help":
                    print("""
Available commands:
- Ask any question or request
- 'agents' - List available agents
- 'generate <topic>' - Generate content about a topic
- 'post <platform> <content>' - Post to a platform
- 'search <query>' - Search social media
- 'quit' - Exit

Examples:
- "Generate a tech tweet about AI"
- "Post twitter Hello world!"
- "Search AI trends"
                    """)
                    continue
                
                if user_input.lower() == "agents":
                    print("\nAvailable agents:")
                    for agent_name in agent.list_agents():
                        print(f"- {agent_name}: {agent.get_agent_description(agent_name)[:100]}...")
                    continue
                
                # Handle special commands
                if user_input.lower().startswith("generate "):
                    topic = user_input[9:]
                    print("🎯 Generating content...")
                    response = await agent.generate_content(topic)
                
                elif user_input.lower().startswith("post "):
                    parts = user_input[5:].split(" ", 1)
                    if len(parts) == 2:
                        platform, content = parts
                        print(f"📤 Posting to {platform}...")
                        response = await agent.post_to_platform(content, platform)
                    else:
                        response = "Usage: post <platform> <content>"
                
                elif user_input.lower().startswith("search "):
                    query = user_input[7:]
                    print("🔍 Searching...")
                    response = await agent.search_content(query)
                
                else:
                    # Regular chat
                    print("💭 Processing...")
                    response = await agent.chat(user_input)
                
                # Display response
                print(f"\n🤖 Agent: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Make sure you have:")
        print("1. Installed mcp-agent: pip install mcp-agent")
        print("2. Set BLACKBOX_API_KEY environment variable")
        print("3. All required MCP servers are available")


if __name__ == "__main__":
    asyncio.run(main())