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

class RephraseRequest(BaseModel):
    instructions: str = "Make it more engaging and professional"

class UpdateStatusRequest(BaseModel):
    status: str  # "approved", "disapproved", "posted", etc.

class ContentResponse(BaseModel):
    id: str
    content: str
    status: str
    message: str

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

@app.post("/content/{content_id}/rephrase", response_model=ContentResponse)
async def rephrase_content(content_id: str, request: RephraseRequest):
    """Rephrase content with given instructions - MOCK IMPLEMENTATION"""
    
    # Mock rephrased content - in real implementation, this would:
    # 1. Fetch original content from MongoDB
    # 2. Send to MCP server for rephrasing with instructions
    # 3. Update content in MongoDB
    # 4. Return updated content
    
    mock_rephrased_content = f"🔄 REPHRASED CONTENT (Mock) - Original content rephrased with instructions: '{request.instructions}'. This would be the actual rephrased content from the MCP server in a real implementation."
    
    return ContentResponse(
        id=content_id,
        content=mock_rephrased_content,
        status="rephrased",
        message="Content successfully rephrased!"
    )

@app.post("/content/{content_id}/approve", response_model=ContentResponse)
async def approve_and_post_content(content_id: str):
    """Approve content and post to social media - MOCK IMPLEMENTATION"""
    
    # Mock approval and posting - in real implementation, this would:
    # 1. Update content status to "approved" in MongoDB
    # 2. Post content to configured social media platforms
    # 3. Update status to "posted" 
    # 4. Return success confirmation
    
    mock_posted_content = f"✅ POSTED CONTENT (Mock) - Content {content_id} has been approved and posted to social media platforms. This is a mock response."
    
    return ContentResponse(
        id=content_id,
        content=mock_posted_content,
        status="posted",
        message="Approved & Posted!"
    )

@app.put("/content/{content_id}/status", response_model=ContentResponse)
async def update_content_status(content_id: str, request: UpdateStatusRequest):
    """Update content status (approve/disapprove/etc) - MOCK IMPLEMENTATION"""
    
    # Mock status update - in real implementation, this would:
    # 1. Validate the status value
    # 2. Update content status in MongoDB
    # 3. Return updated content info
    
    status_messages = {
        "approved": "Content approved successfully!",
        "disapproved": "Content rejected.",
        "pending": "Content status updated to pending.",
        "posted": "Content marked as posted!",
        "draft": "Content saved as draft."
    }
    
    message = status_messages.get(request.status, f"Status updated to: {request.status}")
    
    return ContentResponse(
        id=content_id,
        content=f"📝 CONTENT STATUS UPDATE (Mock) - Content {content_id} status changed to '{request.status}'",
        status=request.status,
        message=message
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
