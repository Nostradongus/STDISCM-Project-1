"""
STDISCM Parallel Programming Project

Image Enhancer

Group 2
- Andre Dominic Ponce
- Joshue Salvador Jadie 

Last Updated: 11/27/22
"""

# Image enhancement libraries
import os        # For accessing directories (folders, etc.)
from math import fabs # For absolute float value conversion
import argparse  # For parsing command line arguments
from PIL import Image, ImageSequence, ImageEnhance # For enhancing images

# Thread synchronization libraries
import threading  # For creating threads
import queue      # For thread-safe queue object
import time       # For time checking, etc.

# System variables
time_limit = 1       # Enhancing time limit (in minutes)
num_threads = 5      # Number of threads that will enhance the images
brightness = 1.0     # Brightness enhancement factor
sharpness = 1.0      # Sharpness enhancement factor
contrast = 1.0       # Contrast enhancement factor
enhanced_images = [] # List of enhanced images

# Global synchronization variables
images = queue.Queue() # Images queue (each element is a list [image data, filename, format / type (extension)])
# TODO: add synchronization variables as needed

# TODO: add parallel programming mechanisms (classes, functions, etc.)

# Gets all images to be enhanced from the specified folder path
def get_images(path):
    # Global image queue
    global images
    
    # Get the image filenames from the folder
    image_files = [filename for filename in os.listdir(path) if os.path.isfile(os.path.join(path, filename))]
    
    # Process each image data
    for image_file in image_files:
        # Get image filename and extension (type / format)
        file_data = image_file.split('.')
        filename = file_data[0]
        ext = file_data[1]
        
        # Get current image data using Pillow
        image = Image.open(f'{path}/{image_file}')
        
        # Place current image data, filename, and type / format in queue
        images.put([image, filename, ext])

# Enhances an image based on the brightness, sharpness, and contrast factors
def enhance_image(image_data):
    print(f'Enhancing {image_data[1]}.{image_data[2]}')
    
    # Global image enhancement factors
    global brightness, sharpness, contrast 
    
    # Check if image is a gif 
    if image_data[2].lower() == 'gif': 
        # Convert gif to RGBA channel format 
        image_data[0] = image_data[0].convert('RGBA')
        
        # Process each frame of the gif
        for frame in ImageSequence.Iterator(image_data[0]):
            # Enhance image based on enhancement factors using Pillow
            enhanced = ImageEnhance.Brightness(frame).enhance(brightness)
            enhanced = ImageEnhance.Sharpness(enhanced).enhance(sharpness)
            enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
            frame = enhanced
    else:
        # Enhance image based on enhancement factors using Pillow
        enhanced = ImageEnhance.Brightness(image_data[0]).enhance(brightness)
        enhanced = ImageEnhance.Sharpness(enhanced).enhance(sharpness)
        enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
        
        # Store enhanced image
        image_data[0] = enhanced
    
    return image_data
    
# Main function
def main(args):
    # Update system variables
    global time_limit, num_threads, brightness, sharpness, contrast
    time_limit = abs(args.time)
    num_threads = abs(args.threads)
    brightness = fabs(args.brightness)
    sharpness = fabs(args.sharpness)
    contrast = fabs(args.contrast)
    
    # Global enhanced images list
    global enhanced_images
    
    # Get all images from specified folder
    get_images(args.images)
    
    # TODO: update algorithm to create threads that will enhance each image for faster processing
    # TODO: include checking of enhancing time limit - to terminate program immediately once reached
    while images.empty() is not True:
        enhanced_images.append(enhance_image(images.get()))
        
    # If specific output folder path does not yet exist, create the folder
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        
    # Save the enhanced images to the output folder
    for image in enhanced_images:
        # if current image is a gif
        if image[2].lower() == 'gif':
            # Get all frames of gif
            current_frame = image[0]
            current_frame.seek(1) # move to second frame
            frames = [frame.copy() for frame in ImageSequence.Iterator(current_frame)]
            
            # save gif
            image[0].save(
                f'{args.output}/{image[1]}.{image[2]}',
                save_all=True,
                append_images=frames,
                duration=100,
                loop=0
            )
        else:
            # save image (jpg or png)
            print(f'{args.output}/{image[1]}.{image[2]}')
            image[0].save(f'{args.output}/{image[1]}.{image[2]}')
    
    # TODO: Add statistics file (number of images enhanced, output folder location, etc.)
    
# Class for defining float range used in argparse
class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return self.start <= other <= self.end
    
if __name__ == "__main__":
    # Get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--images',
                        help='Folder path of the images to be enhanced',
                        required=True)
    parser.add_argument('-o', '--output',
                        help='Folder path to place the enhanced images',
                        default='Results',
                        required=False)
    parser.add_argument('-t', '--time',
                        type=int,
                        help='Enhancing time in minutes; 1 minute by default, converted to absolute value',
                        default='1',
                        required=False)
    parser.add_argument('-b', '--brightness',
                        type=float,
                        help='Brightness enhancement factor',
                        default=1.0,
                        required=False)
    parser.add_argument('-s', '--sharpness',
                        type=float,
                        help='Sharpness enhancement factor',
                        default=1.0,
                        required=False)
    parser.add_argument('-c', '--contrast',
                        type=float,
                        help='Contrast enhancement factor; converted to absolute value',
                        default=1.0,
                        required=False)
    parser.add_argument('-n', '--threads',
                        type=int,
                        help='Number of threads to use, converted to absolute value',
                        default=5,
                        required=False)
    
    args = parser.parse_args() 
    
    main(args)
