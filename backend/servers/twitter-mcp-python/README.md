# Twitter MCP Server - Python Implementation (Updated)

A modern Python implementation of a Twitter MCP (Model Context Protocol) server using FastMCP framework. This server provides comprehensive Twitter functionality including posting tweets, searching tweets, and posting threads.

## Features

- **Post Tweets** - Post individual tweets to Twitter
- **Search Tweets** - Search for tweets using Twitter's search API
- **Post Threads** - Post connected tweet threads with proper reply chaining
- **Modern MCP Implementation** - Uses FastMCP with STDIO transport for compatibility with fast-agent
- **Mock Mode Support** - Automatic fallback to mock responses when credentials are missing
- **Rate Limit Handling** - Built-in rate limit management with tweepy
- **Comprehensive Error Handling** - Proper error handling and user feedback

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
# Twitter API credentials (all required for live mode)
export TWITTER_API_KEY=your_api_key
export TWITTER_API_SECRET_KEY=your_api_secret
export TWITTER_ACCESS_TOKEN=your_access_token
export TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
```

## Running the Server

### With fast-agent (Recommended)

The server is designed to work with fast-agent using STDIO transport:

```bash
# Configure in fastagent.config.yaml
python servers/twitter-mcp-python/server.py
```

### Standalone

```bash
python server.py
```

The server will automatically detect if credentials are available and run in either live or mock mode.

## Available MCP Tools

### post_tweet

Posts a new tweet to Twitter.

**Parameters:**
- `text` (string, required): The content of your tweet (max 280 characters)

**Example:**
```python
await post_tweet("Hello from the Twitter MCP server!")
```

**Response:**
```
Successfully posted tweet! URL: https://twitter.com/status/1565123456789012345
```

### search_tweets

Search for tweets on Twitter using the recent search endpoint.

**Parameters:**
- `query` (string, required): Search query
- `count` (int, optional): Number of tweets to return (10-100, default: 10)

**Example:**
```python
await search_tweets("python MCP", 20)
```

**Response:**
```
Search results for 'python MCP' (15 tweets):

1. @user1 (Display Name)
   Check out this amazing Python MCP server implementation!
   Created: 2025-09-06T18:30:00Z
   URL: https://twitter.com/user1/status/1565123456789012345

2. @user2 (Another User)
   Working on some MCP integrations with Python today...
   Created: 2025-09-06T18:25:00Z
   URL: https://twitter.com/user2/status/1565123456789012346
```

### post_thread

Post a thread of connected tweets to Twitter.

**Parameters:**
- `tweets` (array of strings, required): Array of tweet contents for the thread (each max 280 characters, max 25 tweets)

**Example:**
```python
await post_thread([
    "This is the first tweet in my thread about MCP servers! 🧵",
    "The Model Context Protocol enables AI models to securely connect to external resources and tools.",
    "With Python MCP servers, you can easily integrate Twitter functionality into your AI workflows!"
])
```

**Response:**
```
Successfully posted thread with 3 tweets! First tweet: https://twitter.com/status/1565123456789012345
```

## Configuration with fast-agent

Add to your `fastagent.config.yaml`:

```yaml
mcp:
  servers:
    twitter:
      command: "python"
      args: ["servers/twitter-mcp-python/server.py"]
      env:
        TWITTER_API_KEY: "${TWITTER_API_KEY}"
        TWITTER_API_SECRET_KEY: "${TWITTER_API_SECRET_KEY}" 
        TWITTER_ACCESS_TOKEN: "${TWITTER_ACCESS_TOKEN}"
        TWITTER_ACCESS_TOKEN_SECRET: "${TWITTER_ACCESS_TOKEN_SECRET}"
```

## Mock Mode

If Twitter API credentials are not fully configured, the server automatically operates in mock mode:

- Simulates successful API responses
- Generates mock tweet IDs and timestamps
- Provides realistic response structures for testing
- Logs all mock operations for development visibility

Mock mode is perfect for:
- Development and testing
- Demonstrations without API access
- Validating MCP tool integrations

## Error Handling

The server provides comprehensive error handling:

- **Authentication Errors**: Clear feedback when credentials are invalid
- **Rate Limiting**: Automatic retry with tweepy's built-in rate limit handling
- **Validation Errors**: Input validation with helpful error messages
- **API Errors**: Proper error propagation from Twitter API
- **Network Issues**: Graceful handling of connectivity problems

## Dependencies

- `mcp>=1.2.0` - Modern MCP Python SDK with FastMCP support
- `tweepy>=4.12.0` - Twitter API v2 client library
- `pydantic>=2.0.0` - Data validation and settings management

## Troubleshooting

### Server won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure Python 3.8+ is being used
- Verify the server.py file is executable

### Authentication issues
- Verify all four Twitter API credentials are set correctly
- Check that your Twitter API app has the required permissions (Read and Write)
- Ensure access tokens match the API keys from the same Twitter app

### Mock mode when credentials are set
- Check that all environment variables are properly exported
- Verify there are no typos in environment variable names
- Look for initialization errors in the server logs

### Rate limiting
- The server uses tweepy's built-in rate limit handling
- Wait periods are automatic when limits are exceeded
- Consider reducing request frequency if hitting limits regularly
