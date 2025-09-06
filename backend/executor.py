"""
MCP Client Executor Module

This module provides standardized execution of MCP (Model Context Protocol) clients
across multiple servers with error handling and result standardization.
"""
import os
from typing import List, Optional
from fastmcp.client import Client


class ExecutorResult:
    """Result object for client executor operations"""
    
    def __init__(self, prompt_name: str, server_name: str, content: str = None, 
                 error: str = None, status: str = "generated"):
        self.prompt_name = prompt_name
        self.server_name = server_name
        self.content = content
        self.error = error
        self.status = status

    def __repr__(self):
        return f"ExecutorResult(prompt='{self.prompt_name}', server='{self.server_name}', status='{self.status}')"


def get_mcp_client(server_config: dict, mock_mcp: bool = False):
    """
    Initialize MCP client for a specific server or return mock client
    
    Args:
        server_config: Dictionary containing server configuration
        mock_mcp: Whether to return a mock client instead of real client
        
    Returns:
        MCP client instance (real or mock)
    """
    if mock_mcp:
        class MockClient:
            def __init__(self, server_name):
                self.server_name = server_name
                
            def generate(self, prompt):
                return f"Mock response from {self.server_name} for prompt: {prompt[:50]}..."
                
        return MockClient(server_config.get('type', 'unknown'))
    else:
        return Client(server_config['url'])


def execute_mcp_client(prompt: str, server_names: List[str], config: dict, 
                      prompt_name: str = "custom_prompt", mock_mcp: Optional[bool] = None) -> List[ExecutorResult]:
    """
    Standardized client executor for MCP servers
    
    This function provides a unified interface for executing prompts across
    multiple MCP servers with consistent error handling and result formatting.
    
    Args:
        prompt: The prompt text to send to servers
        server_names: List of server names to execute against
        config: Configuration dictionary containing MCP servers
        prompt_name: Name identifier for the prompt (for logging/tracking)
        mock_mcp: Override mock setting (defaults to environment variable)
        
    Returns:
        List of ExecutorResult objects with results from each server
        
    Example:
        >>> config = load_config()
        >>> results = execute_mcp_client(
        ...     prompt="Write a tweet about AI",
        ...     server_names=["openai", "claude"],
        ...     config=config,
        ...     prompt_name="ai_tweet"
        ... )
        >>> for result in results:
        ...     if result.content:
        ...         print(f"{result.server_name}: {result.content}")
    """
    if mock_mcp is None:
        mock_mcp = os.getenv("MOCK_MCP", "false").lower() == "true"
    
    mcp_servers = config.get('mcp', {}).get('servers', {})
    results = []
    
    for server_name in server_names:
        server_config = mcp_servers.get(server_name)
        
        if not server_config:
            print(f"Warning: Server '{server_name}' not found in config, skipping")
            results.append(ExecutorResult(
                prompt_name=prompt_name,
                server_name=server_name,
                error=f"Server '{server_name}' not found in configuration",
                status="error"
            ))
            continue
            
        try:
            mcp_client = get_mcp_client(server_config, mock_mcp)
            response = mcp_client.generate(prompt=prompt)
            
            results.append(ExecutorResult(
                prompt_name=prompt_name,
                server_name=server_name,
                content=response,
                status="generated" if not mock_mcp else "mock"
            ))
            
        except Exception as e:
            print(f"Error executing '{prompt_name}' on server '{server_name}': {str(e)}")
            results.append(ExecutorResult(
                prompt_name=prompt_name,
                server_name=server_name,
                error=str(e),
                status="error"
            ))
    
    return results


def execute_single_server(prompt: str, server_name: str, config: dict, 
                         prompt_name: str = "single_prompt", mock_mcp: Optional[bool] = None) -> ExecutorResult:
    """
    Execute prompt on a single server (convenience function)
    
    Args:
        prompt: The prompt text to send
        server_name: Name of the server to use
        config: Configuration dictionary
        prompt_name: Name identifier for the prompt
        mock_mcp: Override mock setting
        
    Returns:
        Single ExecutorResult object
    """
    results = execute_mcp_client(prompt, [server_name], config, prompt_name, mock_mcp)
    return results[0] if results else ExecutorResult(
        prompt_name=prompt_name,
        server_name=server_name,
        error="No results returned",
        status="error"
    )


def execute_with_fallback(prompt: str, server_names: List[str], config: dict, 
                         prompt_name: str = "fallback_prompt", mock_mcp: Optional[bool] = None) -> ExecutorResult:
    """
    Execute prompt with fallback pattern - returns first successful result
    
    Args:
        prompt: The prompt text to send
        server_names: List of server names in order of preference
        config: Configuration dictionary
        prompt_name: Name identifier for the prompt
        mock_mcp: Override mock setting
        
    Returns:
        First successful ExecutorResult, or last error if all fail
    """
    results = execute_mcp_client(prompt, server_names, config, prompt_name, mock_mcp)
    
    # Return first successful result
    for result in results:
        if result.content and result.status in ["generated", "mock"]:
            return result
    
    # If all failed, return the last result (which should be an error)
    return results[-1] if results else ExecutorResult(
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
    return [result for result in results if result.content and result.status in ["generated", "mock"]]


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