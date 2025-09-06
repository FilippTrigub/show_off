import os
import yaml
import pymongo
from fastmcp.client import Client
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    repository: str
    event: str
    commit_sha: str
    branch: str

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

@app.post("/generate-content")
async def generate_content(request: GenerateRequest):
    config = load_config()
    prompts_data = load_prompts()

    # Load environment variables for secrets if not set in config
    mongodb_uri = os.getenv("MONGODB_URI") or config['mongodb']['uri']
    mcp_server_url = os.getenv("MCP_SERVER_URL") or config['mcp']['server_url']

    # Initialize MongoDB client
    mongo_client = get_mongodb_client(mongodb_uri)
    db = mongo_client['ai_content_publisher']
    collection = db['contents']

    # Initialize MCP client or mock
    mock_mcp = os.getenv("MOCK_MCP", "false").lower() == "true"
    if mock_mcp:
        class MockClient:
            def generate(self, prompt):
                return f"Mock response for prompt: {prompt}"
        mcp_client = MockClient()
    else:
        mcp_client = Client(mcp_server_url)

    # Load prompts from prompts.yml
    prompts = prompts_data.get('prompts', [])
    if not prompts:
        raise HTTPException(status_code=400, detail="No prompts found in prompts.yml")

    # For now, use the first prompt; can be extended to select based on event
    selected_prompt = prompts[0]['content']

    # Call MCP server to generate content
    response = mcp_client.generate(prompt=selected_prompt)

    if not mock_mcp:
        # Save generated content to MongoDB
        content_doc = {
            "repository": request.repository,
            "event": request.event,
            "commit_sha": request.commit_sha,
            "branch": request.branch,
            "prompt": selected_prompt,
            "content": response,
            "status": "pending_validation"
        }
        collection.insert_one(content_doc)
        return {"message": "Content generated and saved to MongoDB.", "content_id": str(content_doc["_id"])}
    else:
        return {"message": "Content generated (mock mode).", "content": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
