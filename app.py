import schedule
import time
import configparser
import requests
import json
import os
from elasticsearch import Elasticsearch

print("Meme analytics running")

# Debug
debug = False

# Last memes, used to determine whether meme is new
last_memes = {}
last_memes_directory = "last_memes"

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

def save_last_memes(site, memes):
    print("Saving last memes for site {}. Memes are: {}".format(site, memes))
    path = last_memes_directory + "/" + site + ".json"
    os.makedirs(last_memes_directory, exist_ok=True)
    with open(path, 'w+') as f:
        json.dump(memes, f, sort_keys=True, indent=4, separators=(',', ': '))

def load_last_memes():
    global last_memes
    for site in sites:
        path = last_memes_directory + "/" + site + ".json"
        if os.path.isfile(path):
            print("Loading last memes for site {}".format(site))
            with open(path, 'r') as f:
                last_memes[site] = json.load(f)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global sites, es_conn, api, limit_pages, es_index, debug, last_memes_directory
    sites = config.get('main', 'sites', fallback=sites).split(',')
    es_conn = config.get('main', 'es_conn', fallback=es_conn)
    es_index = config.get('main', 'es_index', fallback=es_index)
    limit_pages = config.getint('main', 'limit_pages', fallback=limit_pages)
    debug = config.getboolean('main', 'debug', fallback=debug)
    last_memes_directory = config.get('main', 'last_memes_dir', fallback=last_memes_directory)
    if es_conn is not None:
        es_conn = json.loads(es_conn)
    api = config.get('main', 'api', fallback=api)

def print_config():
    print('Sites to scan: ' + str(sites))
    print('Memes API url: ' + api)
    if es_conn is not None:
        print('Elasticsearch connection url: ' + es_conn)

def is_new(site, meme):
    if site in last_memes:
        for last_meme in last_memes[site]:
            if last_meme == meme:
                return False
    return True

def scan():
    print("Scanning...")
    load_last_memes()
    for site in sites:
        print("Site: " + site)
        page = "/" + site
        page_count = 0
        stop = False
        while stop is not True:
            url = api + page
            page_count += 1

            data = requests.get(url).json()

            if page_count is 1:
                # Save first 3 memes
                # these won't be taken under check in this scan
                save_last_memes(site, data['memes'][0:3])

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
schedule.every(15).seconds.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)