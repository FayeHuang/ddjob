import datetime

from mylib.db import connect_db

def clean(collection):
  collection.delete_many({'updated_time': {'$lt': datetime.datetime.utcnow() - datetime.timedelta(days=2)}})
 
if __name__ == '__main__':
  db = connect_db()
  clean(db["costco_discount"])
  clean(db["costco_latest"])
