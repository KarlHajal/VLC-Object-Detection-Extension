import sys
import os
import cv2
import numpy as np
import tensorflow as tf
import urllib
import tarfile

#sys.path.append("..")

from object_detection.utils import label_map_util

MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
PATH_TO_LABELS = os.path.join('object_detection', 'data', 'mscoco_label_map.pbtxt')
NUM_CLASSES = 90

if(not os.path.exists(MODEL_NAME)):
    print("Downloading " + MODEL_NAME)
    opener = urllib.request.URLopener()
    opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
    tar_file = tarfile.open(MODEL_FILE)
    for file in tar_file.getmembers():
        file_name = os.path.basename(file.name)
        if 'frozen_inference_graph.pb' in file_name:
            tar_file.extract(file, os.getcwd())
    print("File downloaded successfully")


label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

def detect_alert (boxes, classes, scores, category_index, max_boxes_to_draw=20, min_score_thresh=.5,):
    r = []
    for i in range(min(max_boxes_to_draw, boxes.shape[0])):
        if scores is None or scores[i] > min_score_thresh:
            test1 = None
            test2 = None

            if category_index[classes[i]]['name']:
                test1 = category_index[classes[i]]['name']
                test2 = int (100 * scores[i])

            line = {}
            line[test1] = test2
            r.append(line)

    return r

def detect_objects(image_np, sess, detection_graph):
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    (boxes, scores, classes, num_detections) = sess.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor : image_np_expanded})

    alert_array = detect_alert(np.squeeze(boxes), np.squeeze(classes).astype(np.int32), np.squeeze(scores), category_index)

    return alert_array

IMAGE_SIZE = (12, 8)

def load_image_into_numpy_array(image):
    (image_width, image_height) = image.size
    return np.array(image.getdata()).reshape((image_height, image_width, 3)).astype(np.uint8)

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')


def process_image(image, object_name, min_confidence):
    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            alert_array = detect_objects(image, sess, detection_graph)

            for alert in alert_array:
                print(alert)
                if object_name in alert:
                    if alert[object_name] > min_confidence:
                        return True

            return False

object_name = str(sys.argv[2])
object_is_valid = False
for category in category_index:
    if(category_index[category]['name'] == object_name):
        object_is_valid = True
        break
if(not object_is_valid):
    print("Invalid object specified")
    sys.exit()

video_file_name = str(sys.argv[1])
video = cv2.VideoCapture(video_file_name)
success, image = video.read()
frame_count = 0
last_frame = -2
first_frame = -1
success = True
frames_with_object_range = []
while success:
    success,image = video.read()
    print ('Read a new frame: ', success)
    if success:
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if process_image(img, object_name, 87):
            if frame_count > last_frame+1:
                print("Found " + object_name + " at frame " + str(frame_count))
                first_frame = frame_count
            last_frame = frame_count
        else:
            if frame_count == last_frame+1:
                frames_with_object_range.append((first_frame, last_frame))
    frame_count += 1
