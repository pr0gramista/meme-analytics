import schedule
import time
import configparser
import requests
import json
from elasticsearch import Elasticsearch
from elasticsearch import NotFoundError

print("Meme analytics running")

# Debug
debug = False

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
    global sites, es_conn, api, limit_pages, es_index, debug
    sites = config.get('main', 'sites', fallback=sites).split(',')
    es_conn = config.get('main', 'es_conn', fallback=es_conn)
    es_index = config.get('main', 'es_index', fallback=es_index)
    limit_pages = config.getint('main', 'limit_pages', fallback=limit_pages)
    debug = config.getboolean('main', 'debug', fallback=debug)
    if es_conn is not None:
        es_conn = json.loads(es_conn)
    api = config.get('main', 'api', fallback=api)

def print_config():
    print('Sites to scan: ' + str(sites))
    print('Memes API url: ' + api)
    if es_conn is not None:
        print('Elasticsearch connection url: ' + es_conn)

def is_new(meme):
    global es
    try:
        response = es.search(index=es_index, body={"query": {"constant_score": {"filter": {"match_phrase": {"url": meme['url']}}}}})

        if debug:
            print(meme)
            print(response)

        if response['hits']['total'] > 0:
            return response['hits']['hits'][0]['_id']
        else:
            return None
    except NotFoundError:
        return None

def scan_site(site):
    page = "/" + site
    page_count = 0
    stop = False

    # Counters
    memes_indexed = 0
    memes_new = 0
    while stop is not True:
        url = api + page
        page_count += 1

        data = requests.get(url).json()

        for meme in data['memes']:
            mid = is_new(meme)
            es.index(index=es_index, doc_type='meme', body=meme, id=mid)

            if mid is None:
                memes_new += 1
            memes_indexed += 1

            if debug:
                print("Indexed {0} meme (id: {2}) with title: {1}".format(site, meme['title'], mid))

            # Set things for next iteration
            page = data['nextPage']

            if page_count > limit_pages:
                stop = True
                break

    print("Indexed {0} ({1} new) memes for site {2}".format(memes_indexed, memes_new, site))

def scan():
    print("Scanning...")
    for site in sites:
        scan_site(site)

read_config()
print_config()

es = Elasticsearch(hosts=es_conn)

scan()

print("Standby mode")
schedule.every(15).minutes.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)