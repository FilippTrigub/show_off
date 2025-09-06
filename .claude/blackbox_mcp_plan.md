# Blackbox MCP Server Implementation Plan

## Overview
Build an MCP server that provides access to Blackbox AI's API capabilities through standardized MCP tools. The server will run with STDIO transport for easy integration.

## Core Architecture

### MCP Server Framework
- Use FastMCP framework for rapid development
- STDIO transport for hackathon compatibility
- Python-based implementation for simplicity

### Key Components

#### 1. Authentication Tool
- Store and manage Blackbox API key
- Validate API key before making requests
- Handle authentication errors gracefully

#### 2. Chat Completion Tool
- **Function**: `blackbox_chat`
- **Parameters**: 
  - `model`: Model ID (e.g., "blackboxai/openai/gpt-4")
  - `messages`: Array of conversation messages
  - `temperature`: Randomness control (default: 0.7)
  - `max_tokens`: Response length limit (default: 1024)
  - `stream`: Streaming option (default: false)
- **Returns**: Generated response text and metadata

#### 3. Image Generation Tool
- **Function**: `blackbox_image`
- **Parameters**:
  - `prompt`: Image description (max 2K characters)
  - `model`: Image model (default: "blackboxai/black-forest-labs/flux-pro")
- **Returns**: Generated image URL and metadata

#### 4. Model Listing Tool
- **Function**: `blackbox_models`
- **Parameters**: 
  - `type`: Filter by model type (chat, image, video, speech)
- **Returns**: Available models with pricing and capabilities

## Implementation Steps

### Phase 1: Basic Setup
1. Initialize FastMCP server with STDIO transport
2. Set up project structure and dependencies
3. Implement basic error handling and logging

### Phase 2: Core Chat Functionality
1. Implement `blackbox_chat` tool
2. Add API key management
3. Handle Blackbox API authentication
4. Test with basic chat requests

### Phase 3: Image Generation
1. Implement `blackbox_image` tool
2. Handle image generation requests
3. Return image URLs properly formatted

### Phase 4: Utility Tools
1. Add model listing functionality
2. Implement configuration management
3. Add basic health check capabilities

## Technical Requirements

### Dependencies
```python
fastmcp>=1.0.0
httpx>=0.25.0
pydantic>=2.0.0
```

### Environment Variables
- `BLACKBOX_API_KEY`: Required API key for authentication

### Error Handling
- Network failures with retry logic
- API authentication errors
- Rate limiting and quota management
- Invalid parameter validation

## File Structure
```
blackbox-mcp-server/
├── server.py              # Main MCP server entry point
├── blackbox_client.py     # Blackbox API client wrapper
├── tools/
│   ├── chat.py            # Chat completion tool
│   ├── image.py           # Image generation tool
│   └── models.py          # Model listing tool
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
└── README.md             # Usage instructions
```

## Hackathon Considerations
- Focus on working functionality over perfect code
- Skip non-essential features like video/speech generation initially
- Minimal error handling - fail fast and clearly
- Basic logging for debugging
- No complex configuration - use environment variables
- Test with a few key models only

## Success Criteria
- MCP server runs with STDIO transport
- Chat completion works with at least one model
- Image generation produces valid image URLs
- Basic error handling prevents crashes
- Can be integrated with Claude Desktop or other MCP clients

## Future Enhancements (Post-Hackathon)
- Video and speech generation tools
- Advanced streaming support
- Configuration file support
- Comprehensive error handling
- Rate limiting and caching
- Model performance metrics
- Tool parameter validation improvements