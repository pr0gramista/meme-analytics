import tensorflow as tf
import numpy as np
import sys
import configparser


# Does smart things
def read_tensor_from_image_file(file_name, input_height=299, input_width=299, input_mean=0, input_std=255):
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


# Read config
config = configparser.ConfigParser()
config.read('config.ini')
graph_path = config.get('tensorflow', 'graph', fallback="memes_graph.pb")
labels_path = config.get('tensorflow', 'labels', fallback="memes_labels.txt")

# Get image path which we will test
image_path = sys.argv[1]


# Load labels
label_lines = [line.rstrip() for line in tf.gfile.GFile(labels_path)]

# Load graph
graph = tf.Graph()
graph_def = tf.GraphDef()
with open(graph_path, "rb") as f:
    graph_def.ParseFromString(f.read())
with graph.as_default():
    tf.import_graph_def(graph_def)

t = read_tensor_from_image_file(image_path)
input_operation = graph.get_operation_by_name("import/Mul")
output_operation = graph.get_operation_by_name("import/final_result")

with tf.Session(graph=graph) as sess:
    results = sess.run(output_operation.outputs[0],
                       {input_operation.outputs[0]: t})
    results = np.squeeze(results)

    top_k = results.argsort()[-5:][::-1]
    for i in top_k:
        print(label_lines[i], results[i])
