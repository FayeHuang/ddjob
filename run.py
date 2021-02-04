import os
import pymongo
import requests
from bs4 import BeautifulSoup

def fetch_target_product():
  client = pymongo.MongoClient(os.environ["mongodb_url"])
  db = client.dingdong
  products = db.products
  target_product = products.find_one()
  return [target_product]

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
for product in target_products:
  is_arrival = is_product_arrival(product['product_url'])
  if is_arrival:
    print(product['product_url'], 'is_arrival')
  else
    print(product['product_url'], 'not_arrival')
