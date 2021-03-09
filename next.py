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

def get_product_info(product_url, collection):
  r = requests.get(product_url)
  web_content = r.text
  soup = BeautifulSoup(web_content, 'html.parser')
  res = {'product_url': product_url}

  price = soup.select("div.nowPrice span")
  res['price_original'] = price[0].text.strip() if price else None
  
  res['discount'] = None
  
  image = soup.select("section.StyleImages img")
  res['image'] = image[0]['src'] if image else None
  
  title = soup.select("div.Title h1")
  res['title'] = title[0].text.strip() if title else None

  res['description'] = None

  if (is_product_exist(collection, product_url)):
    res['updated_time'] = datetime.datetime.utcnow()
    update_product(collection, res)
  else:
    res['created_time'] = datetime.datetime.utcnow()
    res['updated_time'] = datetime.datetime.utcnow()
    create_product(collection, res)

  return res

def fetch_product_urls(page_url, driver):
  driver.get(page_url)
  driver.refresh()

  # 等待頁面加載完成
  wait = WebDriverWait(driver, 10)
  element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'pageBreak')))

  products = driver.find_elements_by_class_name("Item")
  urls = [p.find_element_by_class_name('TitleText').get_attribute('href') for p in products]
  urls = list(OrderedDict.fromkeys(urls))
  
  page = page_url.split('#')[1].strip()
  # 每一頁有 24 筆資料，會 cache 第一頁和選定的那頁和下一頁 (ex: page=3, 資料會有 page=1,3,4)
  if page == '1_0':
    urls = urls[0:24]
  else:
    urls = urls[24:48] # 撈取當前頁的資料
  # print(len(urls))
  # [print(u) for u in urls]
  return urls
  

def get_boy_product_urls(driver, page_amount):
  res = []
  for i in range(page_amount):
    page = f'https://www.next.tw/zh/shop/department-childrenswear/feat-newin-gender-newbornboys-gender-newbornunisex-gender-youngerboys#{i+1}_0'
    res = res + fetch_product_urls(page, driver)
  return list(OrderedDict.fromkeys(res))

def get_girl_product_urls(driver, page_amount):
  res = []
  for i in range(page_amount):
    page = f'https://www.next.tw/zh/shop/department-childrenswear/feat-newin-gender-newborngirls-gender-newbornunisex-gender-youngergirls#{i+1}_0'
    res = res + fetch_product_urls(page, driver)
  return list(OrderedDict.fromkeys(res))


def run():
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome('chromedriver', options=chrome_options)
  
  product_urls = get_boy_product_urls(driver, 9)
  print("==== begin fetch next boy product ====")
  print(f"共 {len(product_urls)} 筆")
  product_urls.reverse()
  [get_product_info(url, next_boy_collec) for url in product_urls]

  product_urls = get_girl_product_urls(driver, 9)
  print("==== begin fetch next girl product ====")
  print(f"共 {len(product_urls)} 筆")
  product_urls.reverse()
  [get_product_info(url, next_girl_collec) for url in product_urls]

  
if __name__ == '__main__':
  run()