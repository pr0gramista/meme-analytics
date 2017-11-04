# Meme Analytics
The tool for analyzing memes that appear on sites supported by
[Memes-API](https://github.com/PoprostuRonin/memes-api).
Meme Analytics are waiting for new memes (on Memes API) then analyze them and store
information in Elasticsearch instance. You can use Kibana for data visualizing.

## Scripts
`app.py` index memes continuously, does not perform any calculations.

`classifier.py` contains classifier, which simplifies downloading, reading and operating Tensorflow. When run directly can be used to classify given image on path/url.

`run_throught.py` runs throught elasticsearch documents and tries to classify and save the result.
