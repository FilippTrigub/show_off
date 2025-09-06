import os
import yaml
import pymongo
from fastmcp.client import Client
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from pathlib import Path

load_dotenv()

app = FastAPI()

class GenerateRequest(BaseModel):
    repository: str
    commit_sha: str
    branch: str
    summary: str
    timestamp: str  # ISO format

def load_config():
    config_path = Path(__file__).parent.parent / "config.yml"
    with open(str(config_path), "r") as f:
        return yaml.safe_load(f)

def load_prompts():
    prompts_path = Path(__file__).parent / "prompts.yml"
    with open(prompts_path, "r") as f:
        return yaml.safe_load(f)

def get_mongodb_client(uri):
    return pymongo.MongoClient(uri, tlsAllowInvalidCertificates=True)

def get_mcp_client(server_config, mock_mcp=False):
    """Initialize MCP client for a specific server or return mock client"""
    if mock_mcp:
        class MockClient:
            def __init__(self, server_name):
                self.server_name = server_name
            def generate(self, prompt):
                return f"Mock response from {self.server_name} for prompt: {prompt}"
        return MockClient(server_config.get('type', 'unknown'))
    else:
        return Client(server_config['url'])

@app.post("/generate-content")
async def generate_content(request: GenerateRequest):
    config = load_config()
    prompts_data = load_prompts()

    # Load environment variables for secrets if not set in config
    mongodb_uri = os.getenv("MONGODB_URI") or config['mongodb']['uri']
    
    # Initialize MongoDB client for storing commit summary
    mongo_client = get_mongodb_client(mongodb_uri)
    db = mongo_client['ai_content_publisher']
    summaries_collection = db['commit_summaries']
    
    # Store the commit summary with metadata
    summary_doc = {
        "repository": request.repository,
        "commit_sha": request.commit_sha,
        "branch": request.branch,
        "summary": request.summary,
        "timestamp": request.timestamp,
        "created_at": request.timestamp
    }
    summary_result = summaries_collection.insert_one(summary_doc)

    # Load prompts from prompts.yml
    prompts = prompts_data.get('prompts', [])
    if not prompts:
        raise HTTPException(status_code=400, detail="No prompts found in prompts.yml")

    # Get server configurations
    mcp_servers = config.get('mcp', {}).get('servers', {})
    if not mcp_servers:
        raise HTTPException(status_code=400, detail="No MCP servers configured in config.yml")

    mock_mcp = os.getenv("MOCK_MCP", "false").lower() == "true"
    generated_contents = []
    
    # Process each prompt with its designated server
    for prompt_config in prompts:
        prompt_name = prompt_config.get('name', 'unknown')
        prompt_content = prompt_config.get('content', '')
        server_name = prompt_config.get('server', 'blackbox')  # Default to blackbox
        
        # Get server configuration
        server_config = mcp_servers.get(server_name)
        if not server_config:
            print(f"Warning: Server '{server_name}' not found in config, skipping prompt '{prompt_name}'")
            continue
            
        # Initialize MCP client for this server
        try:
            mcp_client = get_mcp_client(server_config, mock_mcp)
            
            # Generate content using the specific server
            response = mcp_client.generate(prompt=prompt_content)
            
            # Prepare metadata for MongoDB MCP server storage
            content_metadata = {
                "repository": request.repository,
                "commit_sha": request.commit_sha,
                "branch": request.branch,
                "summary": request.summary,
                "timestamp": request.timestamp,
                "prompt_name": prompt_name,
                "prompt_content": prompt_content,
                "server_used": server_name,
                "content": response,
                "status": "pending_validation",
                "summary_id": str(summary_result.inserted_id)
            }
            
            generated_contents.append({
                "prompt_name": prompt_name,
                "server_used": server_name,
                "content": response,
                "metadata": content_metadata,
                "status": "generated" if not mock_mcp else "mock"
            })
                
        except Exception as e:
            print(f"Error processing prompt '{prompt_name}' with server '{server_name}': {str(e)}")
            generated_contents.append({
                "prompt_name": prompt_name,
                "server_used": server_name,
                "error": str(e),
                "status": "error"
            })
            continue
    
    return {
        "message": f"Processed {len(generated_contents)} prompts with multiple servers.",
        "summary_id": str(summary_result.inserted_id),
        "commit_info": {
            "repository": request.repository,
            "commit_sha": request.commit_sha,
            "branch": request.branch,
            "summary": request.summary,
            "timestamp": request.timestamp
        },
        "results": generated_contents
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
