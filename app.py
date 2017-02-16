import schedule
import time
import configparser
import requests
import json

print("Meme analytics running")

# Sites to scan
sites = []

# Memes API url
api = 'http://localhost:8080'

# Elasticsearch connection string
es_conn = None

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global sites, es_conn, api
    sites = config.get('main', 'sites', fallback=sites).split(',')
    es_conn = config.get('main', 'es_conn', fallback=es_conn)
    api = config.get('main', 'api', fallback=api)

def print_config():
    print('Sites to scan: ' + str(sites))
    print('Memes API url: ' + api)
    if es_conn is not None:
        print('Elasticsearch connection url: ' + es_conn)

def get_memes(site):
    url = api + '/' + site

    data = requests.get(url).json()
    print(data)

def scan():
    print("I'm working...")

read_config()
print_config()

for site in sites:
    get_memes(site)
schedule.every(5).seconds.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)