import pymongo
import os

MONGODB_URI = os.environ["mongodb_url"]
DB_NAME = "dingdong"
COSTCO_DISCOUNT_COLLECTION = "costco_discount"
COSTCO_LATEST_COLLECTION = "costco_latest"

def connect_db():
    client = pymongo.MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    return db