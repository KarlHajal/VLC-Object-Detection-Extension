import sys
import os
import cv2
import numpy as np
import tensorflow as tf
import urllib
import tarfile
import datetime

#sys.path.append("..")

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

USER = os.environ['USER']
LOCAL_DIR = "/home/"+USER+"/.local/share/vlc/lua/extensions/object_detector_data/"
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
MODEL_DIR = os.path.join(LOCAL_DIR, MODEL_NAME)
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'
PATH_TO_CKPT = MODEL_DIR + '/frozen_inference_graph.pb'
PATH_TO_LABELS = os.path.join(LOCAL_DIR, 'object_detection', 'data', 'mscoco_label_map.pbtxt')
NUM_CLASSES = 90

#Model is downloaded if it isn't found
if(not os.path.exists(MODEL_DIR)):
    print("Downloading " + MODEL_NAME)
    opener = urllib.request.URLopener()
    opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, LOCAL_DIR + MODEL_FILE)
    tar_file = tarfile.open(LOCAL_DIR + MODEL_FILE)
    for file in tar_file.getmembers():
        file_name = os.path.basename(file.name)
        if 'frozen_inference_graph.pb' in file_name:
            tar_file.extract(file, os.getcwd())
    print("File downloaded successfully")


label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Detect recognizable objects in a frame
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

    return alert_array, boxes, scores, classes

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
            alert_array, boxes, scores, classes = detect_objects(image, sess, detection_graph)

            for alert in alert_array:
                print(alert)
                if object_name in alert:
                    if alert[object_name] > min_confidence:
                        vis_util.visualize_boxes_and_labels_on_image_array( image, np.squeeze(boxes), np.squeeze(classes).astype(np.int32), np.squeeze(scores), category_index, use_normalized_coordinates=True, line_thickness=4)
                        #cv2.imshow('object detection', image)
                        #cv2.imwrite("frame.jpg", image)
                        return True

            return False



if(len(sys.argv) < 5):
    print("Wrong number of arguments")
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Wrong number of arguments \n")
    f.close()
    sys.exit()

object_name = str(sys.argv[2])
object_is_valid = False
for category in category_index:
    if(category_index[category]['name'] == object_name):
        object_is_valid = True
        break
if(not object_is_valid):
    print("Invalid object specified")
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Invalid object specified \n")
    f.close()
    sys.exit()

start_time_in_seconds = int(sys.argv[3])
if(start_time_in_seconds < 0):
    print("Invalid frame number specified")
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Invalid timestamp specified \n")
    f.close()
    sys.exit()

previous_frame_contained_object = int(sys.argv[4]) > 0

video_file_name = str(sys.argv[1])
video = cv2.VideoCapture(video_file_name)
success, image = video.read()

fps = int(video.get(cv2.CAP_PROP_FPS)+0.5)
start_frame_number = fps * start_time_in_seconds
video.set(cv2.CAP_PROP_POS_FRAMES, start_frame_number)

frame_count = start_frame_number
last_frame = frame_count - 2 + previous_frame_contained_object
first_frame = frame_count - 1
success = True
while success:
    success,image = video.read()
    print ("Reading frame " + str(frame_count) + ": ", success)
    if success:
        #img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if process_image(image, object_name, 50):
            if frame_count > last_frame+1:
                print("Found " + object_name + " at frame " + str(frame_count))
                cv2.imwrite(LOCAL_DIR + "frame%d.jpg" % frame_count, image) # Save frame as JPEG file

                f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
                f.write(str(frame_count) + "\n")
                f.write(str(datetime.timedelta(seconds=(frame_count/fps))) + "\n")
                f.close()

                #cv2.imwrite("frame.jpg", image) # Save frame as JPEG file
                sys.exit()
            last_frame = frame_count
    else:
        f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
        f.write("Invalid frame number specified \n")
        f.close()
    frame_count += 1

# Object was not found
f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
f.write("No Result \n")
f.close()
