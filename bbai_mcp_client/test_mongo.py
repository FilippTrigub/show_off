import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGODB_URI")
print(f"URI: {uri}")
client = MongoClient(uri)
print("Connected successfully!")
client.close()
