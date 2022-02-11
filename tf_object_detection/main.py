# For running inference on the TF-Hub module.
# https://www.tensorflow.org/hub/tutorials/object_detection
import tensorflow as tf

import tensorflow_hub as hub

# For creating CSV files for design explorer
import pandas as pd

# For downloading the image.
import matplotlib.pyplot as plt
import tempfile
from six.moves.urllib.request import urlopen
from six import BytesIO

# For drawing onto the image.
import numpy as np
from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps

import glob, os, argparse
import multiprocessing

# For measuring the inference time.
import time
from datetime import datetime

# Print Tensorflow version
print(tf.__version__)

# Check available GPU devices.
# print("The following GPU devices are available: %s" % tf.test.gpu_device_name())

from utils import *


def read_args():
    parser=argparse.ArgumentParser()
    parsed, unknown = parser.parse_known_args()
    for arg in unknown:
        if arg.startswith(("-", "--")):
            parser.add_argument(arg)
    pwargs=vars(parser.parse_args())
    print(pwargs)
    return pwargs


def run_detector(detector, img):
    converted_img  = tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]
    start_time = time.time()
    result = detector(converted_img)

    end_time = time.time()

    result = {key:value.numpy() for key,value in result.items()}

    print(datetime.now(), "Found %d objects." % len(result["detection_scores"]), flush = True)
    print(datetime.now(), "Inference time: ", end_time-start_time, flush = True)

    image_with_boxes, n_objects = draw_boxes(
        img.numpy(), result["detection_boxes"],
        result["detection_class_entities"], result["detection_scores"])

    return image_with_boxes, n_objects, max(result["detection_scores"])


if __name__ == '__main__':
    args = read_args()
    load_libs_time = time.time() - int(args['start_time'])
    # By Heiko Gorski, Source: https://commons.wikimedia.org/wiki/File:Naxos_Taverna.jpg
    #image_url = "https://upload.wikimedia.org/wikipedia/commons/6/60/Naxos_Taverna.jpg"
    #downloaded_image_path,img  = download_and_resize_image(image_url, 1280, 856, True)
    #img = tf_load_img(downloaded_image_path)
    processors = int(multiprocessing.cpu_count()/2)

    # Output directory
    odir = args['outdir']
    os.makedirs(odir, exist_ok = True)

    # Find images
    #img_dir = '/mnt/ILSVRC/Data/CLS-LOC/train/n15075141/'
    img_dir = args['imgdir']
    img_path = os.path.join(img_dir, '*.JPEG')
    img_paths = glob.glob(img_path)

    opaths = [ os.path.join(odir, os.path.basename(path)) for path in img_paths ]


    # Load imags:
    # No benefit in using multiprocessing here
    print(datetime.now(), 'Loading images', flush = True)
    start_time = time.time()
    imgs = [ tf_load_img(img_path) for img_path in img_paths ]
    end_time = time.time()
    load_img_time = end_time-start_time
    print(datetime.now(), "Image loading time: ", load_img_time, flush = True)
    # Looks fine display_image(img, path = 'img-loded.jpg') # Looks fine
    # img = tf.image.resize(img, [856, 1280]) # Breaks the image


    # 60 seconds
    # https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1
    module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"
    # 1st: 7 seconds, then 0.15 seconds
    # https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1
    module_handle = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"
    print(datetime.now(), 'Loading model', flush = True)
    detector = hub.load(module_handle).signatures['default']


    # Run detector on images
    imgs_out = []
    n_objs = []
    max_scores = []
    start_time = time.time()
    for img,path in zip(imgs, img_paths):
        print(datetime.now(), 'Processing image: ', path, flush = True)
        image_with_boxes, n_objects, max_score = run_detector(detector, img)
        imgs_out.append(image_with_boxes)
        n_objs.append(n_objects)
        max_scores.append(max_score)

    end_time = time.time()
    detection_time = end_time - start_time
    print(datetime.now(), 'Object detection time: ', detection_time, flush = True)

    del imgs
    del detector

    # Save write images:
    start_time = time.time()
    pool = multiprocessing.Pool(processes=processors)
    pool.map(display_images, zip(imgs_out, opaths))
    #[ display_image(img, path = opath) for img, opath in zip (imgs_out, opaths) ]
    end_time = time.time()
    image_write_time = end_time - start_time
    print(datetime.now(), "Image saving time: ", image_write_time, flush = True)

    # Write down measurements:
    measurements_df = pd.DataFrame(
        {
            'load-libs': [load_libs_time],
            'load-data': [load_img_time],
            'processing': [detection_time],
            'write-data': [image_write_time]
        }
    )
    print(measurements_df)
    measurements_df.to_csv(os.path.join(odir, 'measurements.csv'), index = False)

    # Create CSV file for design explorer:
    # - Each worker creates one file and all files are merged at the end
    # - Format is in:pname,out:pname,img:path
    df = pd.DataFrame(
        {
            'out:max_score': max_scores,
            'out:objects_detected': n_objs,
            'img:original': img_paths,
            'img:processed': opaths
        }
    )
    print(df)
    df.to_csv(os.path.join(odir, 'dex.csv'), index = False)

