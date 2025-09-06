# BBAI MCP Client

This is the MCP Client component for the AI Content Publisher project. It provides an API to generate content using the MCP server and save it to MongoDB.

## Setup

1. Install dependencies using UV:
   ```
   uv sync
   ```

2. Set up environment variables in `.env`:
   ```
   MONGODB_URI=your_mongodb_uri
   MCP_SERVER_URL=your_mcp_server_url
   MOCK_MCP=false
   ```

3. Run the API server:
   ```
   uv run python generate_content.py
   ```

The server will start on http://localhost:8000.

## API Usage

### Generate Content

**Endpoint:** `POST /generate-content`

**Request Body:**
```json
{
  "repository": "owner/repo",
  "event": "push",
  "commit_sha": "abc123",
  "branch": "main"
}
```

**Response:**
```json
{
  "message": "Content generated and saved to MongoDB.",
  "content_id": "object_id"
}
```

The backend can call this endpoint to trigger content generation.

## Configuration

- `config.yml`: General configuration
- `prompts.yml`: Prompts for content generation
