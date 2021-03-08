from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup
import datetime
import os
import pymongo

MONGODB_URI = os.environ["mongodb_url"]
DB_NAME = "dingdong"
COSTCO_DISCOUNT_COLLECTION = "costco_discount"
COSTCO_LATEST_COLLECTION = "costco_latest"

client = pymongo.MongoClient(MONGODB_URI)
db = client[DB_NAME]
costco_discount_collec = db[COSTCO_DISCOUNT_COLLECTION]
costco_latest_collec = db[COSTCO_LATEST_COLLECTION]

def is_product_exist(collection, product_url):
  if collection.find_one({'product_url': product_url}):
    return True
  else:
    return False

def create_product(collection, product_data):
  collection.insert_one(product_data)

def update_product(collection, product_data):
  collection.update_one({'product_url': product_data['product_url']}, {'$set':product_data})

def get_product_info(product_url, collection):
  r = requests.get(product_url)
  web_content = r.text
  soup = BeautifulSoup(web_content, 'html.parser')
  res = {'product_url': product_url}

  price = soup.select("div.price-original span.notranslate")
  res['price_original'] = price[0].text if price else None
  
  discount = soup.select("div.discount span.notranslate")
  res['discount'] = discount[0].text if discount else None
  
  image = soup.find("meta", property="og:image")
  res['image'] = image['content'] if image else None

  title = soup.find("meta", property="og:title")
  res['title'] = title['content'] if title else None

  description = soup.find("meta", property="og:description")
  res['description'] = description['content'] if description else None

  if soup.find(id="addToCartButton"):
    res['arrival'] = True
  else:
    res['arrival'] = False

  if (is_product_exist(collection, product_url)):
    res['updated_time'] = datetime.datetime.utcnow()
    update_product(collection, res)
  else:
    res['created_time'] = datetime.datetime.utcnow()
    res['updated_time'] = datetime.datetime.utcnow()
    create_product(collection, res)

  return res

def run(target_url, collection):
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome('chromedriver', options=chrome_options)
  driver.get(target_url)

  # 等待頁面加載完成
  # refs : https://selenium-python-zh.readthedocs.io/en/latest/waits.html
  try:
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'product-view__option')))
    products = driver.find_elements_by_xpath('//div[@class="product-image"]/a')
    print(f"共 {len(products)} 筆資料")
    count = 1
    for p in products:
      url = p.get_attribute('href')
      get_product_info(url, collection)
      print(f'[ok][{count}] {url}')
      count += 1
  finally:
    driver.quit()

if __name__ == '__main__':
  print("==== 擷取 優惠商品 ====")
  run("https://www.costco.com.tw/c/98", costco_discount_collec)

  print("==== 擷取 最新商品 ====")
  run("https://www.costco.com.tw/c/99", costco_latest_collec)

