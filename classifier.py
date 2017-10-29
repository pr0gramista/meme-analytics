import tensorflow as tf
import numpy as np
import sys
import configparser
import urllib.request as request
import os

class Classifier():
    session = None

    def __init__(self, graph_path, labels_path):
        self.__load_labels(labels_path)
        self.__read_graph(graph_path)

        self.input_operation = self.graph.get_operation_by_name("import/Mul")
        self.output_operation = self.graph.get_operation_by_name("import/final_result")

    def __load_labels(self, labels_path):
        self.label_lines = [line.rstrip() for line in tf.gfile.GFile(labels_path)]

    # Does smart things
    def __read_tensor_from_image_file(self, file_name, input_height=299, input_width=299, input_mean=0, input_std=255):
        input_name = "file_reader"
        output_name = "normalized"
        file_reader = tf.read_file(file_name, input_name)
        if file_name.endswith(".png"):
            image_reader = tf.image.decode_png(file_reader, channels=3, name='png_reader')
        elif file_name.endswith(".gif"):
            image_reader = tf.squeeze(tf.image.decode_gif(file_reader, name='gif_reader'))
        elif file_name.endswith(".bmp"):
            image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
        else:
            image_reader = tf.image.decode_jpeg(file_reader, channels=3, name='jpeg_reader')
        float_caster = tf.cast(image_reader, tf.float32)
        dims_expander = tf.expand_dims(float_caster, 0)
        resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
        normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
        sess = tf.Session()
        result = sess.run(normalized)

        return result

    def __read_graph(self, graph_path):
        graph = tf.Graph()
        graph_def = tf.GraphDef()
        with open(graph_path, "rb") as f:
            graph_def.ParseFromString(f.read())
        with graph.as_default():
            tf.import_graph_def(graph_def)
        self.graph = graph

    def classify(self, image_path):
        session_made = False # Flag whether we want to close session
        if self.session is not None:
            sess = self.session # Session is restored
        else:
            sess = tf.Session(graph=self.graph)
            session_made = True

        t = self.__read_tensor_from_image_file(image_path)

        results = sess.run(self.output_operation.outputs[0],
                           {self.input_operation.outputs[0]: t})
        results = np.squeeze(results)

        if session_made:
            sess.close()

        top_k = results.argsort()[-5:][::-1]

        labels = [self.label_lines[i] for i in top_k]
        values = [results[i] for i in top_k]
        return dict(zip(labels, values))

    def download_and_classify(self, image_url):
        extension = os.path.splitext(image_url)[1]
        path = "classify_image{}".format(extension)
        request.urlretrieve(image_url, path)

        result = self.classify(path)

        os.remove(path) # Remove file

        return result

# Download or read local file and classify
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    graph_path = config.get('tensorflow', 'graph', fallback="memes_graph.pb")
    labels_path = config.get('tensorflow', 'labels', fallback="memes_labels.txt")

    # Get image path which we will test
    image_path = sys.argv[1]

    classifier = Classifier(graph_path, labels_path)
    if image_path.startswith("http"):
        print(classifier.download_and_classify(image_path))
    else:
        print(classifier.classify(image_path))




