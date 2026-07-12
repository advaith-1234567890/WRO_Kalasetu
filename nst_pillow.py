import os
import time
import functools

import PIL.Image
import numpy as np
import matplotlib.pyplot as plt

import tensorflow as tf
import tensorflow_hub as hub

# final display of image function
def tensor_to_image(tensor):
    # If it's a tf.Tensor, convert to numpy, scale to 0-255
    tensor = np.array(tensor * 255, dtype=np.uint8)

    # Remove the batch dimension if it exists
    if np.ndim(tensor) > 3:
        tensor = tensor[0]
    
    return PIL.Image.fromarray(tensor)

# loading image function
def load_image(image_path):
    max_res = 512

    image = tf.io.read_file(image_path)
    image = tf.image.decode_image(image, channels=3)
    image = tf.image.convert_image_dtype(image, tf.float32)

    # Get image shape and calculate scaling factor
    shape = tf.cast(tf.shape(image)[:-1], tf.float32)
    long_side = max(shape)
    scaling_factor = max_res / long_side

    # Corrected the casting and multiplication
    new_shape = tf.cast(shape * scaling_factor, tf.int32)
    
    # Resize and add batch dimension
    image = tf.image.resize(image, new_shape)
    image = image[tf.newaxis, ...] # Corrected slicing syntax

    return image

# running the model and getting the final results
model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

# load_image already returns a tensor, no need to wrap it in tf.constant() again
content_image = load_image('content_image.jpeg')
style_image = load_image('style_image.jpeg')

stylised_image = model(content_image, style_image)[0]

# displaying the image
final_img = tensor_to_image(stylised_image)
final_img.show()  # Opens the image on your machine