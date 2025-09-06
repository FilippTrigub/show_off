"""
FastMCP Executor Module

This module provides parallel execution of AI models/MCP servers using FastMCP
with proper concurrent processing and result standardization.
"""
import asyncio
import subprocess
import os
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from fastmcp import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / '.env')


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


class FastMCPExecutor:
    """
    Parallel executor using FastMCP for concurrent AI model execution
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the FastMCP executor
        
        Args:
            config_path: Path to config (defaults to current directory)
        """
        self.config_path = config_path
        self.server_processes = {}
        self.clients = {}
        self._server_config = {
            "blackbox": {
                "script": "servers/bbai_mcp_server/blackbox_mcp_server/server.py",
                "env": {"BLACKBOX_API_KEY": "${BLACKBOX_API_KEY}"}
            },
            "bluesky": {
                "script": "servers/bluesky-mcp-python/server.py",
                "env": {
                    "BLUESKY_IDENTIFIER": "${BLUESKY_IDENTIFIER}",
                    "BLUESKY_APP_PASSWORD": "${BLUESKY_APP_PASSWORD}",
                    "BLUESKY_SERVICE_URL": "${BLUESKY_SERVICE_URL:-https://bsky.social}",
                    "LOG_RESPONSES": "${LOG_RESPONSES:-false}"
                }
            },
            "linkedin": {
                "script": "servers/linkedin-mcp/linkedin_mcp/server.py",
                "env": {
                    "LINKEDIN_CLIENT_ID": "${LINKEDIN_CLIENT_ID}",
                    "LINKEDIN_CLIENT_SECRET": "${LINKEDIN_CLIENT_SECRET}",
                    "LINKEDIN_REDIRECT_URI": "${LINKEDIN_REDIRECT_URI:-http://localhost:3000/callback}",
                    "LOG_LEVEL": "${LOG_LEVEL:-INFO}"
                }
            },
            "twitter": {
                "script": "servers/twitter-mcp-python/server.py",
                "env": {
                    "TWITTER_API_KEY": "${TWITTER_API_KEY}",
                    "TWITTER_API_SECRET_KEY": "${TWITTER_API_SECRET_KEY}",
                    "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
                    "TWITTER_ACCESS_TOKEN_SECRET": "${TWITTER_ACCESS_TOKEN_SECRET}"
                }
            }
        }
    
    async def _start_server(self, server_name: str) -> bool:
        """Start a single MCP server process"""
        if server_name in self.server_processes:
            return True
            
        server_config = self._server_config.get(server_name)
        if not server_config:
            return False
            
        try:
            # Build environment variables from config
            env = dict(os.environ)
            for key, value in server_config["env"].items():
                # Simple environment variable substitution
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1].split(":-")
                    env_key = env_var[0]
                    default_val = env_var[1] if len(env_var) > 1 else ""
                    env[key] = os.getenv(env_key, default_val)
                else:
                    env[key] = value
            
            # Start the server process
            script_path = Path(__file__).parent / server_config["script"]
            process = await asyncio.create_subprocess_exec(
                "uv run python", str(script_path),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            self.server_processes[server_name] = process
            
            # Give the server a moment to start
            await asyncio.sleep(0.5)
            
            return process.returncode is None
            
        except Exception as e:
            print(f"Failed to start {server_name} server: {e}")
            return False
    
    async def _get_client(self, server_name: str) -> Optional[Client]:
        """Get or create a FastMCP client for the specified server"""
        if server_name not in self.clients:
            server_config = self._server_config.get(server_name)
            if not server_config:
                return None
                
            # Create client with STDIO transport that manages the server process
            from fastmcp.client.transports import StdioTransport
            
            # Use all current environment variables (which now includes .env values)
            env = dict(os.environ)
            
            # Get the script path
            script_path = Path(__file__).parent / server_config["script"]
            
            # Create STDIO transport that will manage the server process
            transport = StdioTransport(
                command="uv",
                args=["run", "python", str(script_path)],
                env=env,
                cwd=str(Path(__file__).parent)
            )
            
            self.clients[server_name] = Client(transport)
                
        return self.clients[server_name]
    
    async def cleanup(self):
        """Clean up all clients (StdioTransport manages server processes automatically)"""
        for client in self.clients.values():
            try:
                await client.close()
            except:
                pass
        
        self.clients.clear()
        self.server_processes.clear()  # Keep for compatibility but not used
    
    async def execute_parallel(self, prompt: str, server_names: List[str], 
                             prompt_name: str = "custom_prompt") -> List[ExecutorResult]:
        """
        Execute prompt across multiple servers/models in parallel
        
        Args:
            prompt: The prompt text to send
            server_names: List of server names to execute against  
            prompt_name: Name identifier for the prompt
            
        Returns:
            List of ExecutorResult objects with results from each server
        """
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
        
        try:
            # Create tasks for parallel execution
            tasks = []
            for server_name in valid_servers:
                task = self._execute_single_server(prompt, prompt_name, server_name)
                tasks.append(task)
            
            # Wait for all tasks to complete
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(parallel_results):
                if isinstance(result, Exception):
                    results.append(ExecutorResult(
                        prompt_name=prompt_name,
                        server_name=valid_servers[i],
                        error=str(result),
                        status="error"
                    ))
                else:
                    results.append(result)
                    
        except Exception as e:
            # If parallel execution fails completely, create error results for all servers
            for server_name in valid_servers:
                results.append(ExecutorResult(
                    prompt_name=prompt_name,
                    server_name=server_name,
                    error=f"Parallel execution failed: {str(e)}",
                    status="error"
                ))
        
        return results
    
    async def _execute_single_server(self, prompt: str, prompt_name: str, server_name: str) -> ExecutorResult:
        """Execute prompt on a single server"""
        import time
        
        start_time = time.time()
        
        try:
            # Get the FastMCP client for this server
            client = await self._get_client(server_name)
            if not client:
                return ExecutorResult(
                    prompt_name=prompt_name,
                    server_name=server_name,
                    error=f"Failed to connect to {server_name} server",
                    status="error"
                )
            
            # Use the client to interact with the server
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                # For simplicity, use a general purpose tool if available
                # In practice, you'd choose the appropriate tool based on the server
                tool_name = None
                if tools:
                    tool_name = tools[0].name
                
                if tool_name:
                    # Call the tool with the prompt
                    response = await client.call_tool(tool_name, {"text": prompt})
                    content = str(response)
                else:
                    # Fallback: just return the prompt as mock response
                    content = f"Mock response for {server_name}: {prompt}"
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                prompt_name=prompt_name,
                server_name=server_name,
                content=content,
                status="generated",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutorResult(
                prompt_name=prompt_name,
                server_name=server_name,
                error=str(e),
                status="error",
                execution_time=execution_time
            )


# Add missing import
import os

# Global executor instance
_executor = None

def get_executor() -> FastMCPExecutor:
    """Get or create the global executor instance"""
    global _executor
    if _executor is None:
        _executor = FastMCPExecutor()
    return _executor


async def execute_mcp_client(prompt: str, server_names: List[str], config: dict, 
                           prompt_name: str = "custom_prompt") -> List[ExecutorResult]:
    """
    Execute prompt across multiple servers/models in parallel using FastMCP
    
    Args:
        prompt: The prompt text to send to servers
        server_names: List of server names to execute against
        config: Configuration dictionary (kept for compatibility, not used with FastMCP)
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
