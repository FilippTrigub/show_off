import os
from typing import List, Dict, Any

from bson import ObjectId
from dotenv import load_dotenv
from pydantic import Field

from mongodb.AsyncMongoDBConnector import AsyncMongoDBConnector
from mongodb.mongodb import MongoModel


class ContentModel(MongoModel):
    """
    Content model with required attributes from GenerateRequest plus content attributes.
    Additional attributes are accepted without validation.
    """
    # Required attributes from GenerateRequest
    repository: str
    commit_sha: str
    branch: str
    summary: str
    timestamp: str  # ISO format

    # Required content attributes
    platform: str
    content: str
    image_content: List[str] = Field(default_factory=list)
    video_content: List[str] = Field(default_factory=list)
    audio_content: List[str] = Field(default_factory=list)

    class Config:
        # Allow extra fields that aren't defined in the model
        extra = "allow"
        # Use field aliases for MongoDB compatibility
        allow_population_by_field_name = True


class ContentController:
    load_dotenv()
    mongodb = AsyncMongoDBConnector(
        database_name=os.environ.get("MONGODB_DB_NAME"),
        collection_name="content")

    async def get_by_id(self, content_id: str, raise_if_none=True) -> ContentModel:
        return ContentModel(**await self.mongodb.find_one_document({"_id": ObjectId(content_id)},
                                                                   raise_if_none=raise_if_none))

    async def get_by(self, key: str, value: str) -> ContentModel:
        return ContentModel(**await self.mongodb.find_one_document({key: value}))

    async def get_all(self) -> List[ContentModel]:
        return [ContentModel(**data) for data in await self.mongodb.find_documents({}, raise_if_none=False)]

    async def get_all_by(self, data: dict, raise_if_none=True) -> List[ContentModel]:
        data = await self.mongodb.find_documents(data, raise_if_none=raise_if_none)
        return [ContentModel(**doc) for doc in data]

    async def create(self, content: ContentModel) -> str:
        created_id = await self.mongodb.create_document(content.model_dump(by_alias=True))
        return created_id

    async def delete_by_id(self, content_id: str) -> bool:
        return await self.mongodb.delete_one_document({"_id": ObjectId(content_id)})

    async def update_by_id(self, content_id: str, update: dict):
        return await self.mongodb.update_one_document({"_id": ObjectId(content_id)}, update, "$set")


load_dotenv()
content_controller = ContentController()
