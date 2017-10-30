import configparser
import json
from elasticsearch import Elasticsearch
import classifier

print("Meme analytics Classify running")

# Debug
debug = False

# Memes API url
api = 'http://memes.pr0gramista.pl:8080/'

# Tensorflow classifier graph and labels
graph_path = "memes_graph.pb"
labels_path = "memes_labels.txt"

# Elasticsearch connection string
es_conn = None
es_index = 'test-index'
es = None


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global es_conn, api, es_index, debug, graph_path, labels_path
    es_conn = config.get('main', 'es_conn', fallback=es_conn)
    es_index = config.get('main', 'es_index', fallback=es_index)
    graph_path = config.get('tensorflow', 'graph', fallback="memes_graph.pb")
    labels_path = config.get('tensorflow', 'labels', fallback="memes_labels.txt")
    debug = config.getboolean('main', 'debug', fallback=debug)
    if es_conn is not None:
        es_conn = json.loads(es_conn)
    api = config.get('main', 'api', fallback=api)


def print_config():
    if es_conn is not None:
        print('Elasticsearch connection url: ' + es_conn)


classifier = classifier.Classifier(graph_path, labels_path)
classifier.start_session()


def process_memes(memes):
    for meme in memes:
        body = meme['_source']
        if body['content']['contentType'] == 'IMAGE':
            global classifier
            print(body['content']['url'])
            result = classifier.download_and_classify(body['content']['url'])
            if result is not None:
                result = {k: v.item() for k, v in
                          result.items()}  # Elasticsearch forces us to convert numpy float to native type
                print(result)

                # Update document
                es.update(index=es_index, doc_type='meme', id=meme['_id'], body={
                    'doc': {
                        'classification': result
                    }
                })


read_config()
print_config()

es = Elasticsearch(hosts=es_conn)

page = es.search(
    index=es_index,
    scroll='2m',
    size=10,
    body={
        # Your query's body
    })
sid = page['_scroll_id']
scroll_size = page['hits']['total']
process_memes(page['hits']['hits'])

while (scroll_size > 0):
    page = es.scroll(scroll_id=sid, scroll='2m')
    sid = page['_scroll_id']

    scroll_size = len(page['hits']['hits'])
    process_memes(page['hits']['hits'])

classifier.end_session()
