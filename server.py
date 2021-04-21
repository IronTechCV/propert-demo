# -*- coding: utf-8 -*-
"""properT-engine-webapp.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15QaXcW83mo5hdVZ4Ou9TQqEsUVdBfBmU
"""

import anvil.server
from anvil import *

anvil.server.connect("M7MDT5AD766C2QZBG6HRWWI4-GTTRJ3MRHDWLKXIO")

#@title Prepare computer vision model

# -*- coding: utf-8 -*-
"""IronTech Object Recognition Engine_modified_by_law
Automatically generated by Colaboratory.
Original file is located at
    https://colab.research.google.com/drive/1CKIwxwexL-Qw55M3YxrLZJFYg2BVml9l
# Setup
Load Tensorflow and stuffs.
"""


import PIL.Image as Image
import io
import requests
import base64

# For running inference on the TF-Hub module.
import tensorflow as tf
import tensorflow_hub as hub

#Suppress tensorflow info and warnings
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

# For downloading the image.
import matplotlib.pyplot as plt
import tempfile
from six.moves.urllib.request import urlopen
from six import BytesIO
import pandas as pd

# For drawing onto the image.
import numpy as np
from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps

# For measuring the inference time.
import time

threshold = 0.2

regulations_df = pd.read_csv('https://raw.githubusercontent.com/propert-cv/propert-demo/main/database.csv')

# Print Tensorflow version
# print(tf.__version__)

# Check available GPU devices.
# print("The following GPU devices are available: %s" % tf.test.gpu_device_name())

"""# Helper functions
Functions for visualisation
"""

def display_image(image):
  fig = plt.figure(figsize=(20, 15))
  plt.grid(False)
  plt.imshow(image)

def display_two_images(image_a, image_b):
  fig = plt.figure(figsize = (20,10))
  fig.add_subplot(1, 2, 1)
  plt.imshow(image_a)
  fig.add_subplot(1, 2, 2)
  plt.imshow(image_b)

def download_and_resize_image(url, new_width=256, new_height=256,
                              display=False):
  _, filename = tempfile.mkstemp(suffix=".jpg")
  response = urlopen(url)
  image_data = response.read()
  image_data = BytesIO(image_data)
  pil_image = Image.open(image_data)
  pil_image = ImageOps.fit(pil_image, (new_width, new_height), Image.ANTIALIAS)
  pil_image_rgb = pil_image.convert("RGB")
  pil_image_rgb.save(filename, format="JPEG", quality=90)
  # print("Image downloaded to %s." % filename)
  if display:
    display_image(pil_image)
  return filename


def draw_bounding_box_on_image(image,
                               ymin,
                               xmin,
                               ymax,
                               xmax,
                               color,
                               font,
                               thickness=4,
                               display_str_list=()):
  """Adds a bounding box to an image."""
  draw = ImageDraw.Draw(image)
  im_width, im_height = image.size
  (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                ymin * im_height, ymax * im_height)
  draw.line([(left, top), (left, bottom), (right, bottom), (right, top),
             (left, top)],
            width=thickness,
            fill=color)

  # If the total height of the display strings added to the top of the bounding
  # box exceeds the top of the image, stack the strings below the bounding box
  # instead of above.
  display_str_heights = [font.getsize(ds)[1] for ds in display_str_list]
  # Each display_str has a top and bottom margin of 0.05x.
  total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)

  if top > total_display_str_height:
    text_bottom = top
  else:
    text_bottom = top + total_display_str_height
  # Reverse list and print from bottom to top.
  for display_str in display_str_list[::-1]:
    text_width, text_height = font.getsize(display_str)
    margin = np.ceil(0.05 * text_height)
    draw.rectangle([(left, text_bottom - text_height - 2 * margin),
                    (left + text_width, text_bottom)],
                   fill=color)
    draw.text((left + margin, text_bottom - text_height - margin),
              display_str,
              fill="black",
              font=font)
    text_bottom -= text_height - 2 * margin

def draw_boxes(image, boxes, class_names, scores, max_boxes=10, min_score=0.1):
  """Overlay labeled boxes on an image with formatted scores and label names."""
  colors = list(ImageColor.colormap.values())

  # try:
  #   font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf",
  #                             25)
  # except IOError:
  #   print("Font not found, using default font.")
  font = ImageFont.load_default()

  for i in range(min(boxes.shape[0], max_boxes)):
    if scores[i] >= min_score:
      ymin, xmin, ymax, xmax = tuple(boxes[i])
      display_str = "{}: {}%".format(class_names[i].decode("ascii"),
                                     int(100 * scores[i]))
      color = colors[hash(class_names[i]) % len(colors)]
      image_pil = Image.fromarray(np.uint8(image)).convert("RGB")
      draw_bounding_box_on_image(
          image_pil,
          ymin,
          xmin,
          ymax,
          xmax,
          color,
          font,
          display_str_list=[display_str])
      np.copyto(image, np.array(image_pil))
  return image

def load_img(path):
  img = tf.io.read_file(path)
  img = tf.image.decode_jpeg(img, channels=3)
  return img

def report(to, obj, problem, regulation):
  print('=================')
  print('Report to:' + to)
  
  # Dropdown box --> [1, 2, 3]
  print("""
  Do you want to create a report?
  1. Yes (Anonymously)
  2. Yes (Not Anonymously)
  3. No
  """)

  choice = input('Please input your choice: ')

  assert int(choice) in [1, 2, 3], "Wrong input"

  if int(choice) == 1:
    f = "Anonymous"
  elif int(choice) == 2:
    f = "User X"
  else:
    return

  print("\n============")
  print("Email Sent")
  print("============")
  print("From:\t" + f)
  print("To:\t" + to)
  print("Subject:\t" + obj)
  print("Problem:\t" + problem)
  print("Regulation:\t" + regulation)

def run_detector(detector, path):
  img = load_img(path)

  converted_img  = tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]
  start_time = time.time()
  result = detector(converted_img)
  end_time = time.time()
  result = {key:value.numpy() for key,value in result.items()}
  
  print("Found %d objects." % len(result["detection_scores"]))
  print("Inference time: ", end_time-start_time)

  image_with_boxes = draw_boxes(
      img.numpy(), result["detection_boxes"],
      result["detection_class_entities"], result["detection_scores"])

  display_two_images(img, image_with_boxes)
  
  print("\nObjects detected: ")
  global all_objs
  all_objs = []
  for cls, score in zip(result["detection_class_entities"], result["detection_scores"]):
    if score > threshold:
      all_objs.append(cls)
  print(all_objs)

  # return image_with_boxes
  import io
  buf = io.BytesIO()
  new_img = Image.fromarray(image_with_boxes)
  new_img.save(buf, format='JPEG')
  byte_im = buf.getvalue()

  import anvil.server
  import anvil.media

  export = anvil.BlobMedia(content_type="image/jpeg", content = byte_im, name="output.jpg")

  return export
  

# from google.colab import drive
# drive.mount('/content/drive')

"""# Load object recognition engine
SSD mobilenet
"""

module_handle = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"
detector = hub.load(module_handle).signatures['default']

#@title Image detection
"""# Detection
Test with images
"""
# for i in image:

@anvil.server.callable
def detect_img(image_url):
  start_time = time.time()
  image_path = download_and_resize_image(image_url, 640, 480)
  output_img = run_detector(detector, image_path)
  end_time = time.time()
  return output_img

detect_img('https://i.imgur.com/xyPtn4m.jpg')

#@title Retrieve provision from legal database
@anvil.server.callable
def recognise_objs():
  interested = []
  if b'Stairs' in all_objs:
    interested.append("Stairs")
  if b'Window' in all_objs:
    interested.append('Window')
  if b'Dog' in all_objs or b'Cat' in all_objs:
    interested.append('Pet')
  return interested

@anvil.server.callable
def get_choices(recognised_obj):
  Subs = regulations_df[regulations_df["item"] == recognised_obj]
  Subs.index = pd.RangeIndex(len(Subs.index))
  outlist = list(Subs["choice"])
  indexlist = list(range(len(Subs["choice"])))
  return dict(zip(outlist, indexlist))

@anvil.server.callable
def output(recognised_obj, c):

  choice_str = str(c)

  Subs = regulations_df[(regulations_df["item"] == recognised_obj) &
                        (regulations_df["choice"] == choice_str)]
  Subs.index = pd.RangeIndex(len(Subs.index))
  
  return Subs.loc[0, "target"], Subs.loc[0, "regulation"], Subs.loc[0, "section"], Subs.loc[0, "text"]

anvil.server.wait_forever()
