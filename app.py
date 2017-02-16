import schedule
import time
import configparser
import requests
import json
from elasticsearch import Elasticsearch

print("Meme analytics running")

# Sites to scan
sites = []

# Limit page index, so our app won't index like 20000 pages (but it could)
limit_pages = 10

# Memes API url
api = 'http://localhost:8080'

# Elasticsearch connection string
es_conn = None
es_index = 'test-index'
es = None

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global sites, es_conn, api, limit_pages, es_index
    sites = config.get('main', 'sites', fallback=sites).split(',')
    es_conn = config.get('main', 'es_conn', fallback=es_conn)
    es_index = config.get('main', 'es_index', fallback=es_index)
    limit_pages = config.get('main', 'limit_pages', fallback=limit_pages)
    if es_conn is not None:
        es_conn = json.loads(es_conn)
    api = config.get('main', 'api', fallback=api)

def print_config():
    print('Sites to scan: ' + str(sites))
    print('Memes API url: ' + api)
    if es_conn is not None:
        print('Elasticsearch connection url: ' + es_conn)

def is_new(site, meme):
    return True #dummy code

def scan():
    print("Scanning...")
    for site in sites:
        print("Site: " + site)
        page = "/" + site
        page_count = 0
        stop = False
        while stop is not True:
            url = api + page
            page_count += 1

            data = requests.get(url).json()

            for meme in data['memes']:
                print(site + " meme: " + meme['title'])
                if is_new(site, meme):
                    es.index(index=es_index, doc_type='meme', body=meme)

                    # Set things for next iteration
                    page = data['nextPage']

                    if page_count > limit_pages:
                        stop = True
                        print("Stopped because of page limit")
                        break
                else:
                    stop = True
                    print("Stopped because meme was old")
                    break

read_config()
print_config()

es = Elasticsearch(hosts=es_conn)

scan()

print("Standby mode")
schedule.every(15).minutes.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)