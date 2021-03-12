from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup
import datetime

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
 
def get_product_info(product_url, arrival, collection):
  r = requests.get(product_url)
  web_content = r.text
  soup = BeautifulSoup(web_content, 'html.parser')
  
  res = {}
  product_id = soup.select("p.product-code span.notranslate")
  res['_id'] = product_id[0].text.strip() if product_id else None
  res['arrival'] = arrival
  res['url'] = 'https://www.costco.com.tw/p/'+res['_id']
  
  discount = soup.select("div.discount span.notranslate")
  res['discount'] = discount[0].text.strip() if discount else None
  
  if not discount:
    price = soup.select("span.product-price-amount span.notranslate")
  else:
    price = soup.select("div.price-after-discount span.you-pay-value")
  res['price'] = price[0].text.strip() if price else None
    
  image = soup.find("meta", property="og:image")
  res['image'] = image['content'] if image else None

  title = soup.find("meta", property="og:title")
  res['title'] = title['content'] if title else None

  description = soup.find("meta", property="og:description")
  res['description'] = description['content'] if description else None

  if (is_product_exist(collection, res['_id'])):
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
    products = driver.find_elements_by_class_name('product-image')
    print(f"共 {len(products)} 筆資料")
    products.reverse()
    count = 1
    for p in products:
      url = p.find_element_by_tag_name('a').get_attribute('href')
      arrival = True
      out_of_stock_status = p.find_elements_by_class_name('out-of-stock-message')
      if len(out_of_stock_status) > 0:
        arrival = False
      get_product_info(url, arrival, collection)
      print(f'[ok][{count}] {url}')
      count = count + 1
  finally:
    driver.quit()

if __name__ == '__main__':
  db = connect_db()
  print("==== 擷取 優惠商品 ====")
  run("https://www.costco.com.tw/c/98", db["costco_discount"])

  print("==== 擷取 最新商品 ====")
  run("https://www.costco.com.tw/c/99", db["costco_latest"])

