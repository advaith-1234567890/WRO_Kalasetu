import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppresses standard TF log output
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Hides oneDNN floating point messages

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR) # Mutes deprecation warnings

import cv2  # Replaced PIL.Image with OpenCV
import numpy as np
import matplotlib.pyplot as plt

import tensorflow as tf
import tensorflow_hub as hub

# deffing var


# final display/save of image function using OpenCV
def tensor_to_image(tensor):
    # Scale to 0-255 and cast to uint8
    tensor = np.array(tensor * 255, dtype=np.uint8)

    # Remove the batch dimension if it exists
    if np.ndim(tensor) > 3:
        tensor = tensor[0]
    
    # TensorFlow uses RGB, but OpenCV uses BGR. We must convert it.
    cv_image = cv2.cvtColor(tensor, cv2.COLOR_RGB2BGR)
    return cv_image

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

    new_shape = tf.cast(shape * scaling_factor, tf.int32)
    
    # Resize and add batch dimension
    image = tf.image.resize(image, new_shape)
    image = image[tf.newaxis, ...] 

    return image

# running the model and getting the final results
model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

content_image = load_image('content_image.jpg')
style_image = load_image('style_image.jpg')

stylised_image = model(content_image, style_image)[0]

# Convert the output tensor to an OpenCV-friendly image
final_img = tensor_to_image(stylised_image)

# Display the image using OpenCV
cv2.imshow('Stylized Image', final_img)

# Optional: Save the image using OpenCV
# cv2.imwrite('stylized_output.jpeg', final_img)

# Wait for a key press to close the window, then clean up
cv2.waitKey(0)
cv2.destroyAllWindows()