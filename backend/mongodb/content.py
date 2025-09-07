import os
from typing import List

from bson import ObjectId
from dotenv import load_dotenv

from mongodb.AsyncMongoDBConnector import AsyncMongoDBConnector


class ContentController:
    mongodb = AsyncMongoDBConnector(
        database_name=os.environ.get("MONGODB_DB_NAME"),
        collection_name="content")

    async def get_by_id(self, course_id: str, raise_if_none=True) -> CourseDAO:
        return CourseDAO(**await self.mongodb.find_one_document({"_id": ObjectId(course_id)},
                                                                raise_if_none=raise_if_none))



    async def get_by(self, key: str, value: str) -> CourseDAO:
        return CourseDAO(**await self.mongodb.find_one_document({key: value}))





    async def get_all(self) -> List[CourseDAO]:
        return [CourseDAO(**data) for data in await self.mongodb.find_documents({}, raise_if_none=False)]

    async def get_all_by(self, data: dict, raise_if_none=True) -> List[CourseDAO]:
        data = await self.mongodb.find_documents(data, raise_if_none=raise_if_none)
        return [CourseDAO(**doc) for doc in data]



    async def create(self, course: CourseDAO) -> str:
        created_id = await self.mongodb.create_document(course.model_dump(by_alias=True))
        return created_id

    async def delete_by_id(self, course_id: str) -> bool:
        return await self.mongodb.delete_one_document({"_id": ObjectId(course_id)})

load_dotenv()
content_controller = ContentController()
