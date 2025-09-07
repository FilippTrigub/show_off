"""
MCP Agent Executor Module

This module provides parallel execution of AI models/MCP servers using mcp-agent
with proper concurrent processing and result standardization.
"""
import asyncio
import os
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / '.env')

# Import mcp-agent components (following llm_agent.py pattern)
from mcp_agent.app import MCPApp
from mcp_agent.config import (
    Settings,
    LoggerSettings,
    MCPSettings,
    MCPServerSettings,
    OpenAISettings,
)
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM


@dataclass
class ExecutorResult:
    """Result object for parallel executor operations"""
    prompt_name: str
    server_name: str
    content: Optional[str] = None
    error: Optional[str] = None
    status: str = "generated"
    execution_time: Optional[float] = None

    def __repr__(self):
        return f"ExecutorResult(prompt='{self.prompt_name}', server='{self.server_name}', status='{self.status}')"


class MCPAgentExecutor:
    """
    MCP Agent Executor using mcp-agent library for LLM-powered execution
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "blackboxai/google/gemini-2.5-pro",
                 base_url: str = "https://api.blackbox.ai/v1"):
        """
        Initialize the MCP Agent executor
        
        Args:
            api_key: BlackboxAI API key (or use BLACKBOX_API_KEY env var)
            model: BlackboxAI model to use
            base_url: BlackboxAI API base URL
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("BLACKBOX_API_KEY")
        if not self.api_key:
            raise ValueError("BlackboxAI API key is required. Set BLACKBOX_API_KEY environment variable.")

        self.model = model
        self.base_url = base_url
        self.app = None

        # Available MCP servers configuration
        self._server_config = {
            "blackbox": {
                "command": "uv",
                "args": ["run", "python", "servers/bbai_mcp_server/blackbox_mcp_server/server.py"],
                "cwd": str(Path(__file__).parent),
                "env": dict(os.environ)
            },
            "bluesky": {
                "command": "uv",
                "args": ["run", "python", "servers/bluesky-mcp-python/server.py"],
                "cwd": str(Path(__file__).parent),
                "env": dict(os.environ)
            },
            "linkedin": {
                "command": "uv",
                "args": ["run", "python", "servers/linkedin-mcp/linkedin_mcp/server.py"],
                "cwd": str(Path(__file__).parent),
                "env": dict(os.environ)
            },
            "twitter": {
                "command": "uv",
                "args": ["run", "python", "servers/twitter-mcp-python/server.py"],
                "cwd": str(Path(__file__).parent),
                "env": dict(os.environ)
            },
            "mongodb": {
                "command": "npx",
                "args": ["-y", "mongodb-mcp-server", "--connectionString",
                         os.getenv("MONGODB_URI"), ],
                "cwd": str(Path(__file__).parent),
                "env": dict(os.environ)
            }
        }
        self._setup_mcp_app()

    def _setup_mcp_app(self):
        """Setup MCP application with server configurations using Settings"""
        # Build server configurations based on requested servers
        mcp_servers = {}
        for server_name, config in self._server_config.items():
            mcp_servers[server_name] = MCPServerSettings(
                command=config["command"],
                args=config["args"],
                cwd=config["cwd"],
                env=config["env"]
            )

        # Create settings with MCP server configurations
        settings = Settings(
            execution_engine="asyncio",
            logger=LoggerSettings(type="console", level="info"),
            mcp=MCPSettings(servers=mcp_servers),
            openai=OpenAISettings(
                api_key=self.api_key,
                base_url=self.base_url,
                default_model=self.model,
            ),
        )

        # Initialize MCP app with settings
        self.app = MCPApp(name="agent_executor", settings=settings)

    async def _create_agent(self, server_names: List[str], app_context):
        """Create agent with access to specified servers following precise pattern from llm_agent.py"""
        agent = Agent(
            name="executor_agent",
            instruction="""You are an AI assistant with access to multiple tools and platforms. You can:
            - Generate content using AI tools (Blackbox)
            - Post and manage content on social media (Twitter, Bluesky, LinkedIn)
            - Search for information and trends
            - Create comprehensive content strategies
            
            Always choose the most appropriate tools for each task and explain your actions.""",
            server_names=server_names
        )
        return agent

    async def cleanup(self):
        """Clean up resources"""
        # mcp-agent handles cleanup automatically through context managers
        pass

    async def execute_parallel(self, prompt: str, server_names: List[str],
                               prompt_name: str = "custom_prompt") -> List[ExecutorResult]:
        """
        Execute prompt across multiple servers using LLM agent following precise llm_agent.py pattern
        
        Args:
            prompt: The prompt text to send
            server_names: List of server names to execute against  
            prompt_name: Name identifier for the prompt
            
        Returns:
            List of ExecutorResult objects with results from each server
        """
        import time
        results = []

        # Filter to valid server names
        valid_servers = []
        for server_name in server_names:
            if server_name in self._server_config:
                valid_servers.append(server_name)
            else:
                results.append(ExecutorResult(
                    prompt_name=prompt_name,
                    server_name=server_name,
                    error=f"Unknown server: {server_name}",
                    status="error"
                ))

        if not valid_servers:
            return results

        start_time = time.time()

        try:
            if not self.app:
                raise RuntimeError("MCP app not initialized")

            # Run the agent with the user message using modern pattern from llm_agent.py
            async with self.app.run() as agent_app:
                agent = await self._create_agent(valid_servers, agent_app)

                # Use the modern attach_llm pattern (settings are already configured in app)
                async with agent:
                    llm = await agent.attach_llm(OpenAIAugmentedLLM)
                    response = await llm.generate_str(prompt)

                    execution_time = time.time() - start_time

                    # Create successful result for all requested servers
                    for server_name in valid_servers:
                        results.append(ExecutorResult(
                            prompt_name=prompt_name,
                            server_name=server_name,
                            content=response,
                            status="generated",
                            execution_time=execution_time
                        ))

        except Exception as e:
            execution_time = time.time() - start_time
            # If execution fails, create error results for all servers
            for server_name in valid_servers:
                results.append(ExecutorResult(
                    prompt_name=prompt_name,
                    server_name=server_name,
                    error=str(e),
                    status="error",
                    execution_time=execution_time
                ))

        return results

    async def _execute_single_server(self, prompt: str, prompt_name: str, server_name: str) -> ExecutorResult:
        """Execute prompt on a single server using LLM agent pattern"""
        # This method is kept for compatibility but now uses the same agent-based approach
        results = await self.execute_parallel(prompt, [server_name], prompt_name)
        return results[0] if results else ExecutorResult(
            prompt_name=prompt_name,
            server_name=server_name,
            error="No results returned",
            status="error"
        )


# Global executor instance
_executor = None


def get_executor() -> MCPAgentExecutor:
    """Get or create the global MCP agent executor instance"""
    global _executor
    if _executor is None:
        _executor = MCPAgentExecutor()
    return _executor


async def execute_mcp_client(
        prompt: str,
        server_names: List[str], config: dict,
        prompt_name: str = "custom_prompt") -> List[ExecutorResult]:
    """
    Execute prompt across multiple servers using MCP agent
    
    Args:
        prompt: The prompt text to send to servers
        server_names: List of server names to execute against
        config: Configuration dictionary (kept for compatibility, not used with mcp-agent)
        prompt_name: Name identifier for the prompt (for logging/tracking)
        
    Returns:
        List of ExecutorResult objects with results from each server
    """
    executor = get_executor()
    try:
        results = await executor.execute_parallel(prompt, server_names, prompt_name)
        return results
    finally:
        # Clean up resources after execution
        await executor.cleanup()


async def execute_single_server(prompt: str, server_name: str, config: dict,
                                prompt_name: str = "single_prompt") -> ExecutorResult:
    """
    Execute prompt on a single server (convenience function)
    
    Args:
        prompt: The prompt text to send
        server_name: Name of the server to use
        config: Configuration dictionary (for compatibility)
        prompt_name: Name identifier for the prompt
        
    Returns:
        Single ExecutorResult object
    """
    results = await execute_mcp_client(prompt, [server_name], config, prompt_name)
    return results[0] if results else ExecutorResult(
        prompt_name=prompt_name,
        server_name=server_name,
        error="No results returned",
        status="error"
    )


async def execute_with_fallback(prompt: str, server_names: List[str], config: dict,
                                prompt_name: str = "fallback_prompt") -> ExecutorResult:
    """
    Execute prompt with parallel execution then return first successful result
    
    Args:
        prompt: The prompt text to send
        server_names: List of server names in order of preference
        config: Configuration dictionary (for compatibility)
        prompt_name: Name identifier for the prompt
        
    Returns:
        First successful ExecutorResult, or last error if all fail
    """
    results = await execute_mcp_client(prompt, server_names, config, prompt_name)

    # Return first successful result
    for result in results:
        if result.content and result.status == "generated":
            return result

    # If all failed, return the first result (which should be an error)
    return results[0] if results else ExecutorResult(
        prompt_name=prompt_name,
        server_name="unknown",
        error="No servers available",
        status="error"
    )


def get_successful_results(results: List[ExecutorResult]) -> List[ExecutorResult]:
    """
    Filter executor results to only include successful ones
    
    Args:
        results: List of ExecutorResult objects
        
    Returns:
        List of successful results only
    """
    return [result for result in results if result.content and result.status == "generated"]


def get_error_summary(results: List[ExecutorResult]) -> str:
    """
    Generate a summary of errors from executor results
    
    Args:
        results: List of ExecutorResult objects
        
    Returns:
        String summary of all errors
    """
    errors = [f"{result.server_name}: {result.error}"
              for result in results if result.error]
    return "; ".join(errors) if errors else "No errors"


def get_performance_summary(results: List[ExecutorResult]) -> Dict[str, float]:
    """
    Generate performance summary from executor results
    
    Args:
        results: List of ExecutorResult objects
        
    Returns:
        Dictionary with performance metrics
    """
    successful = get_successful_results(results)
    if not successful:
        return {"total_time": 0, "fastest": 0, "slowest": 0, "average": 0}

    times = [r.execution_time for r in successful if r.execution_time]
    if not times:
        return {"total_time": 0, "fastest": 0, "slowest": 0, "average": 0}

    return {
        "total_time": max(times),  # Parallel execution time is the slowest
        "fastest": min(times),
        "slowest": max(times),
        "average": sum(times) / len(times),
        "successful_count": len(successful),
        "total_count": len(results)
    }


def validate_server_by_platform(platform: str) -> bool:
    executor = get_executor()
    server = executor._server_config.get(platform.lower())
    return server is not None
