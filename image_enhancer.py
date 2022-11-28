"""
STDISCM Parallel Programming Project

Image Enhancer

Group 2
- Andre Dominic Ponce
- Joshue Salvador Jadie 

Last Updated: 11/28/22
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
output = "Results"   # Output folder name
start_time = 0.0     # Starting time of the program
num_images_input = 0 # Number of input images

# Global shared variables
images = queue.Queue()  # Images queue (each element is a list [image data, filename, format / type (extension)])
num_images_enhanced = 0 # Number of images enhanced by the threads

# Synchronization variables
num_images_enhanced_lock = threading.Lock() # Lock for the number of images enhanced variable

# ImageEnhancer class. Responsible for performing the image enhancing operations.
class ImageEnhancer (threading.Thread):
    def __init__ (self, threadID):
        threading.Thread.__init__(self)
        self.ID = threadID
        self.enhanced_images = 0

    def run (self):
        global num_images_enhanced, num_images_enhanced_lock, time_limit, output
        print(f"Thread {self.ID} is starting...")

        while (images.empty() is not True):
            # Get current time for checking if the time limit has been exceeded already.
            curr_time = time.perf_counter()
            # If time exceeded, break the loop
            if (curr_time > (time_limit * 60)): # Convert time_limit to seconds
                break

            # Get the data of an image from the queue
            curr_image_data = images.get()
            # Enhance the image
            enhanced_image = enhance_image(curr_image_data)

            # Get current time (for printing)
            curr_time = time.perf_counter()
            print(f"[{curr_time}] - [Thread {self.ID}] Enhancing {curr_image_data[1]}.{curr_image_data[2]}")
                
            # If specific output folder path does not yet exist, create the folder
            if not os.path.exists(output):
                os.makedirs(output)
                
            # Save the enhanced image to the output folder
            # If current image is a gif
            if enhanced_image[2].lower() == 'gif':
                # save gif, start from first frame
                enhanced_image[0][0].save(
                    f'{output}/{enhanced_image[1]}.{enhanced_image[2]}',
                    save_all=True,
                    append_images=enhanced_image[0][1:], # append rest of the frames, starting from second frame
                    duration=100,
                    loop=0
                )
            else:
                # save image (jpg or png)
                enhanced_image[0].save(f'{output}/{enhanced_image[1]}.{enhanced_image[2]}')

            # Get current time (for printing)
            curr_time = time.perf_counter()
            print(f'[{curr_time}] - [Thread {self.ID}] Saved image at "{output}/{enhanced_image[1]}.{enhanced_image[2]}"')

            # Increment images enhanced counter of object
            self.enhanced_images += 1

        # Add the total of enhanced images of this object to the global total
        num_images_enhanced_lock.acquire()
        num_images_enhanced += self.enhanced_images
        num_images_enhanced_lock.release()

        print(f"Thread {self.ID} is exiting...")

# Gets all images to be enhanced from the specified folder path
def get_images(path):
    # Global image queue
    global images, num_images_input
    
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

    # Set the number of image inputs
    num_images_input = images.qsize()

# Enhances an image based on the brightness, sharpness, and contrast factors
def enhance_image(image_data):
    # print(f'Enhancing {image_data[1]}.{image_data[2]}')
    
    # Global image enhancement factors
    global brightness, sharpness, contrast 
    
    # Check if image is a gif 
    if image_data[2].lower() == 'gif': 
        # List of enhanced frames
        enhanced_frames = []
        
        # Enhance each frame of the gif
        for frame in ImageSequence.Iterator(image_data[0]):
            # Convert current frame to RGBA channel format
            enhanced = frame.convert('RGBA')
            
            # Enhance current frame based on enhancement factors using Pillow
            if (brightness != 1.0):
                enhanced = ImageEnhance.Brightness(enhanced).enhance(brightness)
            
            if (sharpness != 1.0):
                enhanced = ImageEnhance.Sharpness(enhanced).enhance(sharpness)

            if (contrast != 1.0):
                enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
            
            # Store enhanced current frame
            enhanced_frames.append(enhanced)
            
        # Store list of enhanced frames
        image_data[0] = enhanced_frames
    else:
        # Enhance image based on enhancement factors using Pillow
        if (brightness != 1.0):
            enhanced = ImageEnhance.Brightness(image_data[0]).enhance(brightness)

        if (sharpness != 1.0):
            enhanced = ImageEnhance.Sharpness(enhanced).enhance(sharpness)

        if (contrast != 1.0):
            enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
        
        # Store enhanced image
        image_data[0] = enhanced
    
    return image_data
    
# Main function
def main(args):
    # Update system variables
    global time_limit, num_threads, brightness, sharpness, contrast, output
    time_limit = fabs(args.time)
    num_threads = abs(args.threads)
    brightness = fabs(args.brightness)
    sharpness = fabs(args.sharpness)
    contrast = fabs(args.contrast)
    output = args.output
    
    # Global enhanced images list
    global enhanced_images
    
    # Get all images from specified folder
    get_images(args.images)
    
    # Create threads
    threads = []
    for i in range(num_threads):
        thread = ImageEnhancer(i)
        threads.append(thread)
        thread.start()
    
    # Join threads
    for thread in threads:
        thread.join()
    
    # Display statistics in the console
    finish_time = time.perf_counter()
    print("")
    print(f"Time elapsed: {finish_time - start_time} seconds")
    print(f"No. of input images: {num_images_input}")
    print(f"No. of enhanced images: {num_images_enhanced}")
    print(f"Enhanced images can be found in the {output} folder")

    # Create the statistics text file
    print(f"Creating statistics file...")
    file = open("stats.txt", "w")
    file.write(f"No. of input images: {num_images_input}")
    file.write(f"No. of enhanced images: {num_images_enhanced}")
    file.write(f"Enhanced images can be found in the {output} folder")
    print(f"Statistics file created!")
    
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
                        type=float,
                        help='Enhancing time in minutes; 1 minute by default, converted to absolute value',
                        default='1.0',
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
