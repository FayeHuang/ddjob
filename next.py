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

from mylib.db import connect_db

def is_product_exist(collection, product_id):
  if collection.find_one({'_id': product_id}):
    return True
  else:
    return False

def create_product(collection, product_data):
  collection.insert_one(product_data)

def update_product(collection, product_data):
  collection.update_one({'_id': product_data['_id']}, {'$set': product_data})

def sync_product_db(product, collection):
  if (is_product_exist(collection, product['_id'])):
    product['updated_time'] = datetime.datetime.utcnow()
    update_product(collection, product)
  else:
    product['created_time'] = datetime.datetime.utcnow()
    product['updated_time'] = datetime.datetime.utcnow()
    create_product(collection, product)
  return product

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
    product_id = p.get_attribute('data-itemnumber')
    title = ""
    col_elements = p.find_elements_by_class_name('Col')
    desc_elements = p.find_elements_by_class_name('Desc')
    if len(col_elements) > 0 and len(desc_elements) > 0:
      title = f"{col_elements[0].get_attribute('innerHTML').strip()} - {desc_elements[0].get_attribute('innerHTML').strip()}"
    elif len(col_elements) > 0 and len(desc_elements) == 0:
      title = col_elements[0].get_attribute('innerHTML').strip()
    elif len(col_elements) == 0 and len(desc_elements) > 0:
      title = desc_elements[0].get_attribute('innerHTML').strip()
    else:
      title = p.find_element_by_class_name('TitleText').get_attribute('innerHTML').strip()
    
    price = p.find_element_by_xpath('//div[@class="Price"]/a').get_attribute('innerHTML').strip()
    url = p.find_element_by_class_name('TitleText').get_attribute('href')
    id = url.split('#')[1].strip()
    image = f'https://xcdn.next.co.uk/Common/Items/Default/Default/ItemImages/SearchAlt/224x336/{id}.jpg'
    data = {
      '_id': product_id,
      'url': url,
      'price': price,
      'image': image,
      'title': title,
    }
    res.append(data)
    print(data)
  return res

def get_boy_products(driver, page_amount):
  res = []
  for i in range(page_amount):
    page = f'https://www.next.tw/zh/shop/gender-newbornboys-gender-newbornunisex-gender-olderboys-gender-youngerboys/feat-newin-isort-score#{i+1}_0'
    res = res + fetch_products(page, driver)
  return res

def get_girl_products(driver, page_amount):
  res = []
  for i in range(page_amount):
    page = f'https://www.next.tw/zh/shop/gender-newborngirls-gender-newbornunisex-gender-oldergirls-gender-youngergirls/feat-newin-isort-score#{i+1}_0'
    res = res + fetch_products(page, driver)
  return res

def run():
  db = connect_db()

  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome('chromedriver', options=chrome_options)
  
  print("==== begin fetch next boy product ====")
  products = get_boy_products(driver, 9)
  print(f"共 {len(products)} 筆")
  products.reverse()
  [sync_product_db(product, db["next_boy_latest"]) for product in products]

  print("==== begin fetch next girl product ====")
  products = get_girl_products(driver, 9)
  print(f"共 {len(products)} 筆")
  products.reverse()
  [sync_product_db(product, db["next_girl_latest"]) for product in products]

if __name__ == '__main__':
  run()
