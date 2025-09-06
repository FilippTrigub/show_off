# Bluesky MCP Server (Python)

A Python implementation of the Bluesky MCP server with `create-post` functionality, updated to use the modern MCP Python SDK.

## Features

- **Create Post**: Post content to Bluesky with optional reply functionality
- **Modern MCP SDK**: Uses the latest FastMCP implementation from the official Python MCP SDK
- **Real AT Protocol**: Supports actual Bluesky posting using the atproto library
- **Mock Mode**: Fallback mock mode when credentials are not available
- **STDIO Transport**: Compatible with fast-agent and other MCP clients

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with uv (recommended)
uv add mcp atproto
```

## Environment Variables

Set these environment variables for real Bluesky posting:

```bash
export BLUESKY_IDENTIFIER="your_username.bsky.social"
export BLUESKY_APP_PASSWORD="your_app_password"
export BLUESKY_SERVICE_URL="https://bsky.social"  # Optional, defaults to bsky.social
export LOG_RESPONSES="true"  # Optional, for debugging
```

## Usage

### Direct Execution

```bash
# Run the server directly
python server.py

# Or with uv
uv run server.py
```

### With Fast-Agent

Add to your `fastagent.config.yaml`:

```yaml
mcp:
  servers:
    bluesky_python:
      command: "python"
      args: ["servers/bluesky-mcp-python/server.py"]
      env:
        BLUESKY_IDENTIFIER: "${BLUESKY_IDENTIFIER}"
        BLUESKY_APP_PASSWORD: "${BLUESKY_APP_PASSWORD}"
        BLUESKY_SERVICE_URL: "${BLUESKY_SERVICE_URL:-https://bsky.social}"
        LOG_RESPONSES: "${LOG_RESPONSES:-false}"
```

### Testing with MCP Client

```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_bluesky():
    async with stdio_client(
        StdioServerParameters(
            command="python", 
            args=["servers/bluesky-mcp-python/server.py"]
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", tools)

            # Create a post
            result = await session.call_tool(
                "create_post", 
                {"text": "Hello from the Python MCP server!"}
            )
            print("Post result:", result)

asyncio.run(test_bluesky())
```

## Available Tools

### create_post

Create a new post on Bluesky.

**Parameters:**
- `text` (string, required): The content of your post (max 300 characters)
- `reply_to` (string, optional): URI of post to reply to (format: `at://did:plc:...`)

**Returns:**
- Success message with post URI on success
- Error message on failure

**Example:**
```python
# Simple post
await session.call_tool("create_post", {"text": "Hello Bluesky!"})

# Reply to another post
await session.call_tool("create_post", {
    "text": "This is a reply!",
    "reply_to": "at://did:plc:abcdef123456/app.bsky.feed.post/xyz789"
})
```

## Architecture

- **server.py**: Main MCP server using FastMCP framework
- **bluesky_api.py**: Bluesky API client wrapper using atproto library
- **requirements.txt**: Python dependencies

## Differences from TypeScript Version

This Python implementation:
- Uses the official MCP Python SDK with FastMCP
- Focuses only on the `create-post` tool (no timeline, search, etc.)
- Uses the atproto Python library instead of @atproto/api
- Provides both real and mock implementations
- Uses STDIO transport for compatibility with fast-agent

## Troubleshooting

1. **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`

2. **Login Issues**: 
   - Verify BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD are correct
   - Use app-specific password, not your main account password
   - Check that your account has API access enabled

3. **Mock Mode**: If credentials are missing, server automatically runs in mock mode

4. **Connection Issues**: Check BLUESKY_SERVICE_URL is correct (default: https://bsky.social)

## Development

To contribute or modify:

```bash
# Install with dev dependencies
uv add mcp atproto --dev

# Run with debug logging
LOG_RESPONSES=true python server.py

# Test the implementation
python -m pytest tests/  # If tests are added
```
