import os
from contextlib import asynccontextmanager

import yaml
import pymongo
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from bson import ObjectId
from executor import execute_mcp_client, execute_with_fallback, get_error_summary, get_performance_summary, \
    validate_server_by_platform
from mongodb.content import content_controller, ContentModel

load_dotenv()


def serialize_objectid(item_dict):
    """Helper function to serialize ObjectId fields to strings for JSON"""
    if isinstance(item_dict, dict):
        for key, value in item_dict.items():
            if isinstance(value, ObjectId):
                item_dict[key] = str(value)
            elif isinstance(value, dict):
                serialize_objectid(value)
            elif isinstance(value, list):
                for i, list_item in enumerate(value):
                    if isinstance(list_item, dict):
                        serialize_objectid(list_item)
                    elif isinstance(list_item, ObjectId):
                        value[i] = str(list_item)
    return item_dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run BEFORE startup
    print("App started successfully.")

    yield  # yield the app to the context manager


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class UpdateContentRequest(BaseModel):
    content: str


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

    # Validate MCP server configuration
    mcp_servers = config.get('mcp', {}).get('servers', {})
    if not mcp_servers:
        raise HTTPException(status_code=400, detail="No MCP servers configured in config.yml")

    generated_contents = []

    # Process each prompt with its designated server using the executor
    for prompt_config in prompts:
        prompt_name = prompt_config.get('name', 'unknown')
        prompt_content = prompt_config.get('content', '')
        server_name = prompt_config.get('server', 'blackbox')  # Default to blackbox

        # Execute prompt on specified server
        executor_results = await execute_mcp_client(
            prompt=prompt_content,
            server_names=[server_name],
            config=config,
            prompt_name=prompt_name
        )

        # Process executor results
        for result in executor_results:
            # Prepare metadata for MongoDB MCP server storage
            content_metadata = {
                "repository": request.repository,
                "commit_sha": request.commit_sha,
                "branch": request.branch,
                "summary": request.summary,
                "timestamp": request.timestamp,
                "prompt_name": result.prompt_name,
                "prompt_content": prompt_content,
                "server_used": result.server_name,
                "content": result.content,
                "status": "pending_validation",
                "summary_id": str(summary_result.inserted_id)
            }

            content_result = {
                "prompt_name": result.prompt_name,
                "server_used": result.server_name,
                "status": result.status
            }

            if result.content:
                content_result["content"] = result.content
                content_result["metadata"] = content_metadata

            if result.error:
                content_result["error"] = result.error

            generated_contents.append(content_result)

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
    """Rephrase content with given instructions using MCP client executor"""

    config = load_config()

    # TODO: In real implementation, fetch original content from MongoDB using content_id
    # For now, use placeholder content
    original_content = f"Original content for {content_id} would be fetched from MongoDB"

    # Create rephrase prompt with instructions
    rephrase_prompt = f"""
    Please rephrase the following content according to these instructions: {request.instructions}
    
    Original content:
    {original_content}
    
    Rephrased content:
    """

    # Use executor with fallback pattern - try multiple servers for best result
    rephrase_servers = ["openai", "claude", "blackbox"]  # Prefer language models for rephrasing

    result = await execute_with_fallback(
        prompt=rephrase_prompt,
        server_names=rephrase_servers,
        config=config,
        prompt_name="rephrase_content"
    )

    if result.content and result.status in ["generated", "mock"]:
        # TODO: Update content in MongoDB with rephrased version

        return ContentResponse(
            id=content_id,
            content=result.content,
            status="rephrased",
            message="Content successfully rephrased!"
        )
    else:
        # If all servers failed, return error
        raise HTTPException(status_code=500, detail=f"Failed to rephrase content: {result.error}")


# todo fix first
@app.post("/content/{content_id}/approve", response_model=ContentResponse)
async def approve_and_post_content(content_id: str):
    """Approve content and post to social media using MCP client executor"""

    config = load_config()

    # TODO: In real implementation:
    # 1. Fetch content from MongoDB using content_id
    # 2. Update status to "approved" in MongoDB
    # 3. Use social media MCP servers to post content
    # 4. Update status to "posted"

    content = await content_controller.get_by_id(content_id)

    server_valid = validate_server_by_platform(content.platform)
    if not server_valid:
        raise HTTPException(500, "invalid server")

    # Create posting prompt for social media platforms
    posting_prompt = f"""
    Post this approved content to social media platforms:
    
    Content: {content.content}
    
    Please format appropriately for each platform and return confirmation of posting.
    """

    executor_results = await execute_mcp_client(
        prompt=posting_prompt,
        server_names=[content.platform.lower()],
        config=config,
        prompt_name="approve_and_post"
    )

    # Process posting results
    successful_posts = []
    for result in executor_results:
        if result.content and result.status in ["generated", "mock"]:
            successful_posts.append(f"{result.server_name}: {result.content}")

    if successful_posts:
        # TODO: Update content status to "posted" in MongoDB

        return ContentResponse(
            id=content_id,
            content=f"✅ POSTED: {'; '.join(successful_posts)}",
            status="posted",
            message="Approved & Posted!"
        )
    else:
        # If posting failed, return error but keep content as approved
        error_summary = get_error_summary(executor_results)
        raise HTTPException(status_code=500, detail=f"Failed to post content: {error_summary}")


@app.put("/content/{content_id}/status", response_model=ContentResponse)
async def update_content_status(content_id: str, request: UpdateStatusRequest):
    """Update content status (approve/disapprove/etc) with MongoDB integration"""

    config = load_config()

    # Validate status values
    valid_statuses = ["approved", "disapproved", "pending", "posted", "draft", "pending_validation"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    # TODO: In real implementation:
    # 1. Connect to MongoDB and update content status
    # 2. Handle status-specific logic (e.g., notifications, workflows)
    # 3. Return updated content from database

    # For now, simulate MongoDB update
    try:
        # Load environment variables for MongoDB connection
        mongodb_uri = os.getenv("MONGODB_URI") or config.get('mongodb', {}).get('uri')

        if mongodb_uri and not os.getenv("MOCK_MCP", "false").lower() == "true":
            # In real implementation, would update the actual content document
            mongo_client = get_mongodb_client(mongodb_uri)
            db = mongo_client['ai_content_publisher']
            contents_collection = db['contents']

            # Simulate finding and updating content
            # update_result = contents_collection.update_one(
            #     {"_id": ObjectId(content_id)},
            #     {"$set": {"status": request.status, "updated_at": datetime.utcnow()}}
            # )

            mongo_client.close()

        status_messages = {
            "approved": "Content approved successfully!",
            "disapproved": "Content rejected.",
            "pending": "Content status updated to pending.",
            "posted": "Content marked as posted!",
            "draft": "Content saved as draft.",
            "pending_validation": "Content awaiting validation."
        }

        message = status_messages.get(request.status, f"Status updated to: {request.status}")

        return ContentResponse(
            id=content_id,
            content=f"📝 Status updated for content {content_id} to '{request.status}'",
            status=request.status,
            message=message
        )

    except Exception as e:
        print(f"Error updating content status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@app.get("/content")
async def get_all_content():
    """Get all content items from MongoDB"""
    try:
        content_items = await content_controller.get_all()
        # Convert to dict format for JSON serialization with proper ObjectId handling
        result = []
        for item in content_items:
            item_dict = item.model_dump()
            serialize_objectid(item_dict)
            result.append(item_dict)
        return result
    except Exception as e:
        print(f"Error fetching content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch content: {str(e)}")


@app.get("/content/{content_id}")
async def get_content_by_id(content_id: str):
    """Get specific content item by ID"""
    try:
        content_item = await content_controller.get_by_id(content_id, raise_if_none=True)
        item_dict = content_item.model_dump()
        serialize_objectid(item_dict)
        return item_dict
    except Exception as e:
        print(f"Error fetching content by ID: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Content not found: {str(e)}")


@app.put("/content/{content_id}/status")
async def update_content_status_endpoint(content_id: str, request: UpdateStatusRequest):
    """Update content status using ContentController"""
    try:
        # Validate status values
        valid_statuses = ["pending_validation", "approved", "rejected", "published", "pending", "disapproved", "posted"]
        if request.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        # Update status using update_by_id
        await content_controller.update_by_id(content_id, {"status": request.status})

        # Get updated content to return
        updated_content = await content_controller.get_by_id(content_id, raise_if_none=True)

        status_messages = {
            "approved": "Content approved successfully!",
            "rejected": "Content rejected.",
            "pending_validation": "Content status updated to pending validation.",
            "published": "Content marked as published!",
            "posted": "Content marked as posted!",
            "pending": "Content status updated to pending.",
            "disapproved": "Content disapproved."
        }

        message = status_messages.get(request.status, f"Status updated to: {request.status}")

        return ContentResponse(
            id=content_id,
            content=updated_content.content,
            status=getattr(updated_content, 'status', request.status),
            message=message
        )

    except Exception as e:
        print(f"Error updating content status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@app.put("/content/{content_id}/update")
async def update_content_text(content_id: str, request: UpdateContentRequest):
    """Update content text using ContentController"""
    try:
        # Update content using update_by_id
        await content_controller.update_by_id(content_id, {"content": request.content})

        # Get updated content to return
        updated_content = await content_controller.get_by_id(content_id, raise_if_none=True)

        return ContentResponse(
            id=content_id,
            content=updated_content.content,
            status=getattr(updated_content, 'status', "updated"),
            message="Content updated successfully!"
        )

    except Exception as e:
        print(f"Error updating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update content: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
