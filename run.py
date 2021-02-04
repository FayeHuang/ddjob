import os
import pymongo

client = pymongo.MongoClient(os.environ["mongodb_url"])
db = client.dingdong
products = db.products
target_product = products.find_one()
print(target_product)
