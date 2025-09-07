# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Content Publisher project with three main components:
- **Frontend**: React/TypeScript application with Vite and TailwindCSS for content approval interface
- **Backend**: FastAPI application that generates content using MCP and stores in MongoDB  
- **MCP Server**: Blackbox AI MCP server providing AI model access

## Development Commands

### Frontend (React/Vite)
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production (TypeScript compile + Vite build)
npm run lint         # Run ESLint with TypeScript support
npm run preview      # Preview production build
```

### Backend (FastAPI)
```bash
cd backend
uv sync              # Install dependencies
uv run python main.py  # Start FastAPI server on port 8001
uv run pytest       # Run tests (test_main.py, test_mongo.py)
```

### MCP Server (Blackbox AI)
```bash
cd bbai_mcp_server
uv sync              # Install dependencies  
uv run blackbox-mcp-server  # Start MCP server with STDIO transport
```

## Architecture

### Component Communication Flow
1. **Frontend** → **Backend**: POST /generate-content with repository event data
2. **Backend** → **MCP Server**: Content generation via fastmcp client
3. **Backend** → **MongoDB**: Store generated content with validation status
4. **Frontend**: Display content for approval/disapproval

### Key Files
- `backend/main.py`: FastAPI server with content generation endpoint
- `backend/config.yml`: Configuration for MongoDB URI and MCP server URL
- `backend/prompts.yml`: Content generation prompts
- `frontend/src/App.tsx`: Main React component with post approval interface
- `bbai_mcp_server/blackbox_mcp_server/`: MCP server implementation

### Environment Setup
Backend requires these environment variables:
```bash
MONGODB_URI=your_mongodb_connection_string
MCP_SERVER_URL=your_mcp_server_url
MOCK_MCP=false  # Set to "true" for development without MCP server
```

MCP Server requires:
```bash
BLACKBOX_API_KEY=your_blackbox_ai_api_key
```

## Testing
- Backend: Uses pytest for API and MongoDB integration tests
- Frontend: Uses Vite's built-in testing capabilities
- Run `uv run pytest` in backend directory for backend tests

## Package Management
- Root project: Uses `uv` (Python package manager) with `uv.lock`
- Frontend: Uses `npm` with `package-lock.json`
- MCP Server: Uses `uv` with separate `pyproject.toml`