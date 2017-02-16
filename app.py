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

def get_memes(site, page):
    if page == 0:
        url = api + '/' + site
    else:
        url = api + '/' + site + '/' + str(page)

    data = requests.get(url).json()
    return data['memes']

def scan():
    print("I'm working...")

read_config()
print_config()

es = Elasticsearch(hosts=es_conn)

for site in sites:
    fail = False
    page = 0
    while fail is False:
        memes = get_memes(site, page)

        for meme in memes:
            # if is_new:
            es.index(index=es_index, doc_type='meme', body=meme)
            print(meme)
            # else
            #   break or something like that

        page += 1
        if page > limit_pages:
            fail = True


schedule.every(5).seconds.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)