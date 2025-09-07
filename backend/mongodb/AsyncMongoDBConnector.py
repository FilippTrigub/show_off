import os
from datetime import timezone, datetime
from typing import List, Dict, Union, Optional

from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi


class AsyncMongoDBConnector:
    """
    This class provides basic CRUD operations for a MongoDB database.
    It is agnostic of the business logic and data models.
    """

    def __init__(self, collection_name: str, database_name: str, uri: str = None) -> None:
        load_dotenv()
        self.uri = uri or os.environ.get("MONGODB_URI")
        self.client = AsyncIOMotorClient(
            self.uri,
            server_api=ServerApi("1"),
            maxIdleTimeMS=300000,  # 5 minutes
            connectTimeoutMS=30000,  # 30 seconds
            serverSelectionTimeoutMS=30000,  # 30 seconds
        )
        self.database_name = database_name
        self.collection_name = collection_name
        self.collection = self.client[self.database_name][self.collection_name]
        print(f"Connected to MongoDB at {self.uri}. "
                         f"Using database: {self.database_name} and collection: {self.collection_name}.")

    async def create_document(self, document: dict) -> str:
        """
        Insert a new document into a collection.
        """
        try:
            document = self._preprocess(document)
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            raise Exception(f"Error while inserting document into MongoDB: {e.__repr__()}")

    async def find_one_document(self,
                                query: dict,
                                projection: dict = None,
                                raise_if_none=True,
                                max_time_ms: Optional[int] = None) -> Union[Dict, None]:
        """
        Retrieve a single document from a collection.
        """
        try:
            query = self._preprocess(query)
            document = await self.collection.find_one(query, projection, max_time_ms=max_time_ms)
            if not document and raise_if_none:
                raise Exception(is_warning=True,
                                       message=f"No document found for query: {query} in collection {self.collection_name}")
            return document or None
        except PyMongoError as e:
            raise Exception(f"Error while retrieving document from MongoDB: {e.__repr__()}")

    async def find_documents(self, query: dict,
                             projection: dict = None,
                             limit: int = None,
                             sort_field: str = None,
                             raise_if_none=True) -> List[dict]:
        """
        Retrieve all documents from a collection that match the query.
        """
        try:
            query = self._preprocess(query)
            cursor = self.collection.find(query, projection)
            if sort_field:
                cursor = cursor.sort(sort_field, -1)
            documents = await cursor.to_list(length=limit)
            if not documents and raise_if_none:
                raise Exception(is_warning=True,
                                       message=f"No documents found for query: {query} in collection {self.collection_name}")
            return documents or []
        except PyMongoError as e:
            raise Exception(f"Error while retrieving document from MongoDB: {e.__repr__()}")

    async def insert_one_document(self, insert_data: dict) -> str:
        """
        Insert a document into a collection.
        """
        try:
            doc_id = await self.collection.insert_one(insert_data)
            return str(doc_id.inserted_id)
        except PyMongoError as e:
            raise Exception("Error while inserting conversation data into MongoDB: {}".format(str(e)))

    async def update_one_document(self, query: dict, update_data: dict, operator: str) -> bool:
        """
        Update a document in a collection.
        """
        try:
            query = self._preprocess(query)
            result = await self.collection.update_one(query, {operator: update_data})
            await self.update_last_updated(query)
            return result.acknowledged and result.matched_count == 1
        except PyMongoError as e:
            raise Exception(f"Error while updating document in MongoDB: {e.__repr__()}")

    async def update_many_documents(self,
                                    query: dict,
                                    update: Union[list, dict],
                                    array_filters: List[dict] = None) -> bool:
        try:
            query = self._preprocess(query)
            result = await self.collection.update_many(
                query,
                update,
                array_filters=array_filters
            )
            return result.modified_count > 0 or result.acknowledged
        except PyMongoError as e:
            raise Exception(f"Error while updating documents in MongoDB: {e.__repr__()}")

    async def delete_one_document(self, query: dict) -> bool:
        """
        Delete a document from a collection.
        """
        try:
            query = self._preprocess(query)
            result = await self.collection.delete_one(query)
            return result.acknowledged
        except PyMongoError as e:
            raise Exception(f"Error while deleting document from MongoDB: {e.__repr__()}")

    async def delete_documents(self, query: dict) -> bool:
        """
        Delete a document from a collection.
        """
        try:
            query = self._preprocess(query)
            result = await self.collection.delete_many(query)
            return result.deleted_count > 0
        except PyMongoError as e:
            raise Exception(f"Error while deleting document from MongoDB: {e.__repr__()}")

    @staticmethod
    def _preprocess(query: dict) -> dict:
        if query and query.get('_id') and type(query['_id']) not in [ObjectId]:
            if type(query['_id']) is str:
                query['_id'] = ObjectId(query['_id'])
            elif type(query['_id']) is dict:
                if len(query['_id'].keys()) == 1 and '$in' in query['_id'].keys():
                    query['_id']['$in'] = [ObjectId(id) for id in query['_id']['$in']]
            else:
                raise Exception(f"Invalid _id format: {query['_id']}")
        return query

    async def update_last_updated(self, query):
        await self.collection.update_one(
            query,
            {"$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
