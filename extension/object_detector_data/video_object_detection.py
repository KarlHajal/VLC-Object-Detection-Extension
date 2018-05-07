import sys
import os
import cv2
import numpy as np
import tensorflow as tf
import urllib
import tarfile
import datetime

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

# VLC extension directory.
USER = os.environ['USER']
LOCAL_DIR = "/home/"+USER+"/.local/share/vlc/lua/extensions/object_detector_data/"

# What model to download.
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
MODEL_DIR = os.path.join(LOCAL_DIR, MODEL_NAME)
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_DIR + '/frozen_inference_graph.pb'

# List of the strings that is used to add a correct label to each box.
PATH_TO_LABELS = os.path.join(LOCAL_DIR, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

# Size, in inches of the output images.
IMAGE_SIZE = (12, 8)

# Model is downloaded if it isn't found.
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

# Load a (frozen) Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

# Loading the label map : it maps indices to category names (e.g. 5 -> airplane)
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Helper code
def load_image_into_numpy_array(image):
    (image_width, image_height) = image.size
    return np.array(image.getdata()).reshape((image_height, image_width, 3)).astype(np.uint8)

# Detects whether objects were found after a search and returns a dict mapping objects to scores
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

# Runs a search for objects on a given image in a numpy array representation
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

# Runs the object detection on an image and checks the search's output for objects that were found
# If the desired object is found and its score is greater than the minimum required, it returns true
def process_image(image, object_name, min_confidence):
    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            alert_array, boxes, scores, classes = detect_objects(image, sess, detection_graph)

            for alert in alert_array:
                print(alert)
                if object_name in alert:
                    if alert[object_name] > min_confidence:
                        vis_util.visualize_boxes_and_labels_on_image_array( image, np.squeeze(boxes), np.squeeze(classes).astype(np.int32), np.squeeze(scores), category_index, use_normalized_coordinates=True, line_thickness=4) # Overlay bounding boxes and scores on top of the image
                        return True

            return False



# 4 arguments should be passed:
# 1- Path to a video file
# 2- Name of an object to search for
# 3- Start time of the search in the video file (in seconds)
# 4- Whether the first frame should be included in the search
if(len(sys.argv) < 5):
    print("Wrong number of arguments")
    # Write the error message to an output file
    # The output file is only written when the execution is over every time
    # because the lua script uses the fact that it was written to know that
    # this script has concluded its execution
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Wrong number of arguments \n")
    f.close()
    sys.exit()

object_name = str(sys.argv[2])
object_is_valid = False
# Check if the specified object is supported by the model
for category in category_index:
    if(category_index[category]['name'] == object_name):
        object_is_valid = True
        break
if(not object_is_valid):
    print("Invalid object specified")
    # Write the error message to an output file
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Invalid object specified \n")
    f.close()
    sys.exit()

start_time_in_seconds = int(sys.argv[3])
# Check if the specified start time is invalid
# Checking if it's greater than the video file's length
# is done later when the video file is read
if(start_time_in_seconds < 0):
    print("Invalid frame number specified")
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Invalid timestamp specified \n")
    f.close()
    sys.exit()

# Check if the first frame should be included in the search
# This was added to make room for a feature that would allow the user
# to continue the search from where it left off and not keep repeating a series of
# consecutive frames that contain the object since this is more than likely not desirable
previous_frame_contained_object = int(sys.argv[4]) > 0

# Path to the video file
video_file_name = str(sys.argv[1])
video = cv2.VideoCapture(video_file_name)
success, image = video.read() # Check if the path is valid and read the file
if not success :
    f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
    f.write("Could not read video file \n")
    f.close()
    sys.exit()

fps = int(video.get(cv2.CAP_PROP_FPS)+0.5) # Video file's frames per second
start_frame_number = fps * start_time_in_seconds # Find the number of the frame corresponding to the time in seconds
video.set(cv2.CAP_PROP_POS_FRAMES, start_frame_number) # Set the video's position to the corresponding frame

# Those were added to make room for the feature described above, where the user would
# be able to continue the search from where it left off
frame_count = start_frame_number
last_frame = frame_count - 2 + previous_frame_contained_object
first_frame = frame_count - 1

# Start searching the video file for objects frame by frame
while success:
    success,image = video.read()
    print ("Reading frame " + str(frame_count) + ": ", success)
    if success:
        # Frame was read successfully
        if process_image(image, object_name, 50): # Object was found in the frame
            if frame_count > last_frame+1: # Allows skipping consecutive frames containing the same object if the continue feature is added
                print("Found " + object_name + " at frame " + str(frame_count))

                cv2.imwrite(LOCAL_DIR + "frame%d.jpg" % frame_count, image) # Save frame as JPEG file

                f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+') # Save search result in output file
                f.write(str(frame_count) + "\n")
                f.write(str(datetime.timedelta(seconds=(frame_count/fps))) + "\n")
                f.close()

                sys.exit() # Exit since all we need is the first frame containing the object
            last_frame = frame_count
    else:
        # Frame was not read successfully
        f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
        f.write("Invalid frame number specified \n")
        f.close()
    frame_count += 1

# Object was not found
f = open(LOCAL_DIR + 'object_detection_output.txt', 'w+')
f.write("No Result \n")
f.close()
