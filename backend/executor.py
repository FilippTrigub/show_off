"""
Fast-Agent Executor Module

This module provides parallel execution of AI models/MCP servers using fast-agent
with proper concurrent processing and result standardization.
"""
import asyncio
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from mcp_agent.core.fastagent import FastAgent


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


class FastAgentExecutor:
    """
    Parallel executor using fast-agent for concurrent AI model execution
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the FastAgent executor
        
        Args:
            config_path: Path to fastagent.config.yaml (defaults to current directory)
        """
        self.config_path = config_path or Path(__file__).parent / "fastagent.config.yaml"
        self.fast_agent = FastAgent("AI Content Executor")
        self._setup_agents()
    
    def _setup_agents(self):
        """Setup fast-agent configurations for different servers/models"""
        
        # Define agents for different AI models/servers
        @self.fast_agent.agent(
            "blackbox_agent",
            "You are a helpful AI assistant powered by Blackbox AI. Provide accurate and concise responses.",
            servers=["blackbox"]
        )
        async def blackbox_handler():
            pass
        
        @self.fast_agent.agent(
            "bluesky_agent",
            "You are a helpful assistant for Bluesky social media platform. Provide engaging social media content.",
            servers=["bluesky"]
        )
        async def bluesky_handler():
            pass
            
        @self.fast_agent.agent(
            "linkedin_agent",
            "You are a professional LinkedIn assistant. Provide business-oriented content and insights.",
            servers=["linkedin"]
        )
        async def linkedin_handler():
            pass
            
        @self.fast_agent.agent(
            "twitter_agent",
            "You are a Twitter assistant. Provide concise and engaging content suitable for the platform.",
            servers=["twitter"]
        )
        async def twitter_handler():
            pass
        
        # Define parallel workflow for concurrent execution
        @self.fast_agent.parallel(
            name="concurrent_executor",
            fan_out=["blackbox_agent", "bluesky_agent", "linkedin_agent", "twitter_agent"]
        )
        async def parallel_execution():
            pass
    
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
        
        # Map server names to agent names
        server_agent_map = {
            "blackbox": "blackbox_agent",
            "bluesky": "bluesky_agent", 
            "linkedin": "linkedin_agent",
            "twitter": "twitter_agent"
        }
        
        # Filter to requested agents
        requested_agents = []
        for server_name in server_names:
            agent_name = server_agent_map.get(server_name)
            if agent_name:
                requested_agents.append(agent_name)
            else:
                results.append(ExecutorResult(
                    prompt_name=prompt_name,
                    server_name=server_name,
                    error=f"Unknown server: {server_name}",
                    status="error"
                ))
        
        if not requested_agents:
            return results
        
        try:
            # Execute in parallel using fast-agent
            async with self.fast_agent.run() as agent:
                # Create tasks for parallel execution
                tasks = []
                for agent_name in requested_agents:
                    server_name = next(k for k, v in server_agent_map.items() if v == agent_name)
                    task = self._execute_single_agent(agent, agent_name, prompt, prompt_name, server_name)
                    tasks.append(task)
                
                # Wait for all tasks to complete
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(parallel_results):
                    if isinstance(result, Exception):
                        server_name = next(k for k, v in server_agent_map.items() if v == requested_agents[i])
                        results.append(ExecutorResult(
                            prompt_name=prompt_name,
                            server_name=server_name,
                            error=str(result),
                            status="error"
                        ))
                    else:
                        results.append(result)
                        
        except Exception as e:
            # If parallel execution fails completely, create error results for all servers
            for server_name in server_names:
                if server_name in server_agent_map:
                    results.append(ExecutorResult(
                        prompt_name=prompt_name,
                        server_name=server_name,
                        error=f"Parallel execution failed: {str(e)}",
                        status="error"
                    ))
        
        return results
    
    async def _execute_single_agent(self, agent, agent_name: str, prompt: str, 
                                   prompt_name: str, server_name: str) -> ExecutorResult:
        """Execute prompt on a single agent"""
        import time
        
        start_time = time.time()
        
        try:
            # Get the specific agent and send the prompt
            agent_instance = getattr(agent, agent_name)
            response = await agent_instance.send(prompt)
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                prompt_name=prompt_name,
                server_name=server_name,
                content=str(response),
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


# Global executor instance
_executor = None

def get_executor() -> FastAgentExecutor:
    """Get or create the global executor instance"""
    global _executor
    if _executor is None:
        _executor = FastAgentExecutor()
    return _executor


async def execute_mcp_client(prompt: str, server_names: List[str], config: dict, 
                           prompt_name: str = "custom_prompt") -> List[ExecutorResult]:
    """
    Execute prompt across multiple servers/models in parallel using fast-agent
    
    Args:
        prompt: The prompt text to send to servers
        server_names: List of server names to execute against
        config: Configuration dictionary (kept for compatibility, not used with fast-agent)
        prompt_name: Name identifier for the prompt (for logging/tracking)
        
    Returns:
        List of ExecutorResult objects with results from each server
    """
    executor = get_executor()
    results = await executor.execute_parallel(prompt, server_names, prompt_name)
    return results


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
