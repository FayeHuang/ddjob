from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup
import datetime
import os
import pymongo
from collections import OrderedDict

MONGODB_URI = os.environ["mongodb_url"]
DB_NAME = "dingdong"
NEXT_BOY_COLLECTION = "next_boy_latest"
NEXT_GIRL_COLLECTION = "next_girl_latest"

client = pymongo.MongoClient(MONGODB_URI)
db = client[DB_NAME]
next_boy_collec = db[NEXT_BOY_COLLECTION]
next_girl_collec = db[NEXT_GIRL_COLLECTION]

def is_product_exist(collection, product_url):
  if collection.find_one({'product_url': product_url}):
    return True
  else:
    return False

def create_product(collection, product_data):
  collection.insert_one(product_data)

def update_product(collection, product_data):
  collection.update_one({'product_url': product_data['product_url']}, {'$set':product_data})

def sync_product_db(product, collection):
  if (is_product_exist(collection, product['product_url'])):
    res['updated_time'] = datetime.datetime.utcnow()
    update_product(collection, res)
  else:
    res['created_time'] = datetime.datetime.utcnow()
    res['updated_time'] = datetime.datetime.utcnow()
    create_product(collection, res)
  return res

def fetch_products(page_url, driver):
  driver.get(page_url)
  driver.refresh()

  # 等待頁面加載完成
  wait = WebDriverWait(driver, 10)
  element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'pageBreak')))

  products = driver.find_elements_by_class_name("Item")
  page = page_url.split('#')[1].strip()
  # 每一頁有 24 筆資料，會 cache 第一頁和選定那頁的下一頁 (ex: page=3, 資料會有 page=1,3,4)
  if page == '1_0':
    products = products[0:24]
  else:
    products = products[24:48] # 撈取當前頁的資料
  
  res = []
  for p in products:
    name1 = p.find_element_by_class_name('Col').get_attribute('innerHTML').strip()
    name2 = p.find_element_by_class_name('Desc').get_attribute('innerHTML').strip()
    price = p.find_element_by_xpath('//div[@class="Price"]/a').get_attribute('innerHTML').strip()
    url = p.find_element_by_class_name('TitleText').get_attribute('href')
    id = url.split('#')[1].strip()
    image = f'https://xcdn.next.co.uk/Common/Items/Default/Default/ItemImages/SearchAlt/224x336/{id}.jpg'
    data = {
      'product_url': url,
      'price_original': price,
      'image': image,
      'title': f'{name1} - {name2}',
    }
    res.append(data)
    print(data)
  return res

def get_boy_products(driver, page_amount):
  res = []
  for i in range(page_amount):
    page = f'https://www.next.tw/zh/shop/department-childrenswear/feat-newin-gender-newbornboys-gender-newbornunisex-gender-youngerboys#{i+1}_0'
    res = res + fetch_products(page, driver)
  return res

def get_girl_products(driver, page_amount):
  res = []
  for i in range(page_amount):
    page = f'https://www.next.tw/zh/shop/department-childrenswear/feat-newin-gender-newborngirls-gender-newbornunisex-gender-youngergirls#{i+1}_0'
    res = res + fetch_products(page, driver)
  return res

def run():
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome('chromedriver', options=chrome_options)
  
  products = get_boy_products(driver, 9)
  print("==== begin fetch next boy product ====")
  print(f"共 {len(products)} 筆")
  products.reverse()
  [sync_product_db(product, next_boy_collec) for product in products]

  products = get_girl_products(driver, 9)
  print("==== begin fetch next girl product ====")
  print(f"共 {len(products)} 筆")
  products.reverse()
  [sync_product_db(product, next_girl_collec) for product in products]
