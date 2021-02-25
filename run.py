import os
import pymongo
import requests
from bs4 import BeautifulSoup
import datetime

MONGODB_URI = os.environ["mongodb_url"]
DB_NAME = "dingdong"
PRODUCT_COLLECTION = "products"
USER_COLLECTION = "users"

client = pymongo.MongoClient(MONGODB_URI)
db = client[DB_NAME]
product_collec = db[PRODUCT_COLLECTION]
user_collec = db[USER_COLLECTION]

def fetch_target_product():
  return list(product_collec.find( { "arrival": False } ))

def get_user_notify_token(userId):
  target_user = user_collec.find_one({'userId': userId})
  if 'notifyToken' in target_user.keys():
    return target_user['notifyToken']
  else:
    return None

def is_product_arrival(target_url):
  r = requests.get(target_url)
  web_content = r.text
  soup = BeautifulSoup(web_content, 'html.parser')
  addToCartButton = soup.find(id="addToCartButton")
  if addToCartButton:
    return True
  else:
    return False

target_products = fetch_target_product()
target_users = {}
for product in target_products:
  # 判斷商品是否到貨
  product_url = product['product_url']
  is_arrival = is_product_arrival(product_url)
  # 推播訊息
  message = ""
  if is_arrival:
    message = f"🥳 商品已經到貨 !!\n{product_url}"
    product_collec.update_one(
      { "product_url": product_url },
      { "$set": { "updated_time": datetime.datetime.utcnow(), "arrival":True }}
    )
  else:
    message = f"😞 商品還沒到貨\n{product_url}"
    product_collec.update_one(
      { "product_url": product_url },
      { "$set": { "updated_time": datetime.datetime.utcnow() }}
    )
  # 取得推播 token
  userId = product['userId']
  notify_token = None
  if userId not in target_users.keys():
    notify_token = get_user_notify_token(userId)
    target_users[userId] = notify_token
  else:
    notify_token = target_users[userId]
  # 發送推播
  r = requests.post(
        'https://notify-api.line.me/api/notify', 
        data = { 'message': message },
        headers = { 'Authorization': f"Bearer {notify_token}"}
      )
  if r.status_code == 200:
    print(f"推播成功,{userId},{product_url},{is_arrival}")
  else:
    print(f"推播失敗,{userId},{product_url},{is_arrival}")
