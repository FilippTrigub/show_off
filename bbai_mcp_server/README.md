# Blackbox MCP Server

An MCP (Model Context Protocol) server that provides access to Blackbox AI's API capabilities through standardized tools.

## Features

- **Chat Completion**: Access to various chat models including GPT-4, Claude 3, and Mistral
- **Image Generation**: Generate images using Flux Pro and Stable Diffusion models
- **Model Listing**: Browse available models and their capabilities
- **Connection Testing**: Validate API connectivity and authentication

## Quick Start

### 1. Installation

```bash
cd bbai_mcp_server
uv sync
```

### 2. Configuration

Set your Blackbox AI API key as an environment variable:

```bash
export BLACKBOX_API_KEY="your_api_key_here"
```

Get your API key from the [Blackbox AI dashboard](https://www.blackbox.ai/).

### 3. Run the Server

```bash
uv run blackbox-mcp-server
```

The server runs with STDIO transport for MCP client integration.

## Available Tools

### `blackbox_chat`
Send chat completion requests to Blackbox AI models.

**Parameters:**
- `model` (string, required): Model ID (e.g., "blackboxai/openai/gpt-4")
- `messages` (array, required): List of message objects with "role" and "content"
- `temperature` (float, optional): Randomness control (0.0-2.0, default: 0.7)
- `max_tokens` (integer, optional): Maximum response length (default: 1024)
- `stream` (boolean, optional): Stream response (default: false)

**Example:**
```json
{
  "model": "blackboxai/openai/gpt-4",
  "messages": [
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 256
}
```

### `blackbox_image`
Generate images using Blackbox AI image models.

**Parameters:**
- `prompt` (string, required): Image description (max 2K characters)
- `model` (string, optional): Image model (default: "blackboxai/black-forest-labs/flux-pro")

**Example:**
```json
{
  "prompt": "A futuristic city with flying cars at sunset",
  "model": "blackboxai/black-forest-labs/flux-pro"
}
```

### `blackbox_models`
List available Blackbox AI models.

**Parameters:**
- `model_type` (string, optional): Filter by type ("chat", "image", "video", "speech")

### `test_connection`
Test API connectivity and authentication.

**Returns:** Connection status and API key validation.

## Popular Models

### Chat Models
- `blackboxai/openai/gpt-4` - GPT-4
- `blackboxai/anthropic/claude-3-sonnet` - Claude 3 Sonnet
- `blackboxai/mistral/mistral-small` - Mistral Small

### Image Models
- `blackboxai/black-forest-labs/flux-pro` - Flux Pro
- `blackboxai/stability-ai/stable-diffusion` - Stable Diffusion

## Integration with MCP Clients

### Claude Desktop
Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "blackbox": {
      "command": "uv",
      "args": ["run", "blackbox-mcp-server"],
      "cwd": "/path/to/bbai_mcp_server",
      "env": {
        "BLACKBOX_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Error Handling

The server includes comprehensive error handling for:
- Invalid API keys (401 errors)
- Rate limiting (429 errors)
- Network failures
- Invalid parameters
- API response parsing errors

## Development

### Project Structure
```
bbai_mcp_server/
├── blackbox_mcp_server/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── blackbox_client.py # Blackbox API client
│   ├── tools.py           # Tool implementations
│   └── config.py          # Configuration management
├── pyproject.toml         # Project configuration
└── README.md
```

### Running Tests
```bash
uv run pytest
```

## Troubleshooting

### "Invalid API key" Error
- Verify your `BLACKBOX_API_KEY` environment variable is set
- Check that your API key is valid in the Blackbox AI dashboard
- Ensure the key hasn't expired

### "Connection failed" Error
- Check your internet connection
- Verify the Blackbox AI API is accessible
- Try the `test_connection` tool to diagnose issues

### Import Errors
- Run `uv sync` to install all dependencies
- Ensure you're using Python 3.8 or higher

## License

MIT License - feel free to use in your hackathon projects!