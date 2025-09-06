#!/usr/bin/env python
"""
FastMCP CLI Script

This script starts up FastMCP clients connected to local Python MCP servers
and provides a simple command-line interface to interact with them.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from fastmcp import Client
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Create rich console for nice formatting
console = Console()

class FastMCPCLI:
    """Simple CLI for interacting with FastMCP clients connected to local servers"""
    
    def __init__(self):
        """Initialize the FastMCP CLI"""
        self.server_processes = {}
        self.clients = {}
        self._server_config = {
            "blackbox": {
                "script": "servers/bbai_mcp_server/blackbox_mcp_server/server.py",
                "env": {"BLACKBOX_API_KEY": os.getenv("BLACKBOX_API_KEY", "")}
            },
            # "bluesky": {
            #     "script": "servers/bluesky-mcp-python/server.py",
            #     "env": {
            #         "BLUESKY_IDENTIFIER": os.getenv("BLUESKY_IDENTIFIER", ""),
            #         "BLUESKY_APP_PASSWORD": os.getenv("BLUESKY_APP_PASSWORD", ""),
            #         "BLUESKY_SERVICE_URL": os.getenv("BLUESKY_SERVICE_URL", "https://bsky.social"),
            #         "LOG_RESPONSES": os.getenv("LOG_RESPONSES", "false")
            #     }
            # },
            # "linkedin": {
            #     "script": "servers/linkedin-mcp/linkedin_mcp/server.py",
            #     "env": {
            #         "LINKEDIN_CLIENT_ID": os.getenv("LINKEDIN_CLIENT_ID", ""),
            #         "LINKEDIN_CLIENT_SECRET": os.getenv("LINKEDIN_CLIENT_SECRET", ""),
            #         "LINKEDIN_REDIRECT_URI": os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:3000/callback"),
            #         "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO")
            #     }
            # },
            # "twitter": {
            #     "script": "servers/twitter-mcp-python/server.py",
            #     "env": {
            #         "TWITTER_API_KEY": os.getenv("TWITTER_API_KEY", ""),
            #         "TWITTER_API_SECRET_KEY": os.getenv("TWITTER_API_SECRET_KEY", ""),
            #         "TWITTER_ACCESS_TOKEN": os.getenv("TWITTER_ACCESS_TOKEN", ""),
            #         "TWITTER_ACCESS_TOKEN_SECRET": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
            #     }
            # }
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
            env.update(server_config["env"])
            
            # Start the server process
            script_path = Path(__file__).parent / server_config["script"]
            console.print(f"[cyan]Starting {server_name} server: {script_path}[/]")
            
            process = await asyncio.create_subprocess_exec(
                "python", str(script_path),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            self.server_processes[server_name] = process
            
            # Give the server a moment to start
            await asyncio.sleep(1.0)
            
            if process.returncode is None:
                console.print(f"[green]✓ Started {server_name} server[/]")
                return True
            else:
                console.print(f"[red]✗ Failed to start {server_name} server[/]")
                return False
            
        except Exception as e:
            console.print(f"[red]Failed to start {server_name} server: {e}[/]")
            return False
    
    async def _get_client(self, server_name: str) -> Client:
        """Get or create a FastMCP client for the specified server"""
        if server_name not in self.clients:
            # Start the server if not already running
            if not await self._start_server(server_name):
                raise RuntimeError(f"Failed to start {server_name} server")
                
            # Create client connected to the server process
            process = self.server_processes[server_name]
            if process:
                self.clients[server_name] = Client(process)
            else:
                raise RuntimeError(f"No process for {server_name} server")
                
        return self.clients[server_name]
    
    async def start_all_servers(self):
        """Start all available servers"""
        console.print("[cyan]Starting all MCP servers...[/]")
        
        for server_name in self._server_config.keys():
            await self._start_server(server_name)
            
        console.print(f"[green]Started {len(self.server_processes)} servers[/]")
    
    async def cleanup(self):
        """Clean up all server processes and clients"""
        console.print("[cyan]Cleaning up servers...[/]")
        
        for client in self.clients.values():
            try:
                await client.close()
            except:
                pass
        
        for server_name, process in self.server_processes.items():
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
                console.print(f"[yellow]Terminated {server_name} server[/]")
            except asyncio.TimeoutError:
                process.kill()
                console.print(f"[red]Killed {server_name} server[/]")
            except:
                pass
        
        self.clients.clear()
        self.server_processes.clear()
    
    async def start_cli(self):
        """Start the interactive CLI"""
        console.print("\n[bold magenta]========================================[/]")
        console.print("[bold magenta]    FastMCP Multi-Server CLI            [/]")
        console.print("[bold magenta]========================================[/]")
        
        try:
            # Start all servers
            await self.start_all_servers()
            
            if not self.server_processes:
                console.print("[bold red]No servers started. Check configuration and credentials.[/]")
                return
            
            console.print(f"[bold green]FastMCP clients ready for {len(self.server_processes)} servers![/]")
            console.print("[yellow]Type 'exit' or 'quit' to end the session[/]")
            console.print("[yellow]Available servers: " + ", ".join(self.server_processes.keys()) + "[/]")
            
            # Main chat loop
            while True:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/]")
                
                # Check for exit command
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                
                # Check for server-specific commands
                if user_input.startswith("@"):
                    # Server-specific command: @server_name command
                    parts = user_input[1:].split(" ", 1)
                    if len(parts) == 2:
                        server_name, command = parts
                        if server_name in self.server_processes:
                            await self._handle_server_command(server_name, command)
                        else:
                            console.print(f"[bold red]Unknown server: {server_name}[/]")
                    else:
                        console.print("[bold yellow]Usage: @server_name command[/]")
                    continue
                
                # Send to all servers
                await self._handle_broadcast_command(user_input)
                
        except Exception as e:
            console.print(f"[bold red]Error starting CLI: {str(e)}[/]")
        finally:
            await self.cleanup()
    
    async def _handle_server_command(self, server_name: str, command: str):
        """Handle a command for a specific server"""
        try:
            client = await self._get_client(server_name)
            
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                if not tools:
                    console.print(f"[bold yellow]{server_name}: No tools available[/]")
                    return
                
                # Use the first available tool (for simplicity)
                tool = tools[0]
                console.print(f"[cyan]Calling {tool.name} on {server_name}...[/]")
                
                # Call the tool with the command
                response = await client.call_tool(tool.name, {"text": command})
                
                # Display the response
                console.print(f"\n[bold green]{server_name.title()} Response[/]")
                console.print(Panel(
                    str(response),
                    title=f"{server_name} - {tool.name}",
                    expand=False
                ))
                
        except Exception as e:
            console.print(f"[bold red]Error with {server_name}: {str(e)}[/]")
    
    async def _handle_broadcast_command(self, command: str):
        """Handle a command sent to all servers"""
        console.print(f"[cyan]Broadcasting to all servers: {command}[/]")
        
        tasks = []
        for server_name in self.server_processes.keys():
            task = self._handle_server_command(server_name, command)
            tasks.append(task)
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    # Create and start the CLI
    cli = FastMCPCLI()
    await cli.start_cli()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]FastMCP CLI terminated by user[/]")
        sys.exit(0)
