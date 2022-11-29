"""
STDISCM Parallel Programming Project

Image Enhancer

Group 2
- Andre Dominic Ponce
- Joshue Salvador Jadie 

Tom & Jerry Images Source:
https://www.kaggle.com/datasets/balabaskar/tom-and-jerry-image-classification

GIF Source:
https://www.kaggle.com/datasets/raingo/tumblr-gif-description-dataset

Last Updated: 11/29/22
"""

# General libraries
import os              # For accessing directories (folders, etc.)
from math import fabs  # For absolute float value conversion
import argparse        # For parsing command line arguments
import uuid            # For generating UUIDs; for printing the current run's ID for statistics

# Image enhancement library
from PIL import Image, ImageSequence, ImageEnhance

# Thread synchronization libraries
import threading        # For creating threads
import queue            # For thread-safe queue object
from queue import Empty # Exception to determine if queue is already empty
import time             # For time checking, etc.

# System variables
time_limit = 1                    # Enhancing time limit (in minutes)
num_threads = 5                   # Number of threads that will enhance the images
brightness = 1.0                  # Brightness enhancement factor
sharpness = 1.0                   # Sharpness enhancement factor
contrast = 1.0                    # Contrast enhancement factor
output = "Results"                # Output folder name
formats = ['jpg', 'png', 'gif']   # Accepted image types / formats
start_time = time.perf_counter()  # Starting time of the program
num_images_input = 0              # Number of input images

# Global shared variables
# Images queue (each element is a list [input path, image filename, image format / type (extension)])
images = queue.Queue()
# Number of images enhanced by the threads
num_images_enhanced = 0

# Synchronization variables
# Lock for the number of images enhanced variable
num_images_enhanced_lock = threading.Lock()

# ImageEnhancer thread class. Responsible for performing the image enhancing operations.
class ImageEnhancer(threading.Thread):
    # Constructor
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.ID = threadID
        self.enhanced_images = 0

    # Instructions that the ImageEnhancer thread will do once it runs
    def run(self):
        global images, num_images_enhanced, num_images_enhanced_lock, time_limit, output, start_time
        print(f"Thread {self.ID} is starting...")

        # Repeat until no more images to be enhanced
        while images.empty() is not True:
            # If time limit exceeded, break the loop
            if check_time_exceeded(time.perf_counter()):
                break

            # Get the data of an image from the queue
            # Stop operation after 2 seconds since it is possible that there are no more images in the queue
            try:
                curr_image_data = images.get(timeout = 2) 
            except Empty:
                break

            # Enhance the image
            enhanced_image_data = enhance_image(curr_image_data)
            
            # If time limit exceeded after image enhancement, stop operation
            if check_time_exceeded(time.perf_counter()):
                break

            # Get current time in seconds after image enhancement (for printing)
            print(f"[{get_curr_time()}] - [Thread {self.ID}] Enhancing {curr_image_data[1]}.{curr_image_data[2]}")

            # Save the enhanced image to the output folder
            # If current image is a gif
            if enhanced_image_data[2].lower() == 'gif':
                # Save gif frames, start from first frame
                enhanced_image_data[3][0].save(
                    f'{output}/{enhanced_image_data[1]}.{enhanced_image_data[2]}',
                    save_all=True,
                    # append rest of the frames, starting from second frame
                    append_images=enhanced_image_data[3][1:],
                    duration=100,
                    loop=0
                )
            else:
                # Save image (jpg or png)
                enhanced_image_data[3].save(f'{output}/{enhanced_image_data[1]}.{enhanced_image_data[2]}')

            # Get current time in seconds (for printing)
            print(
                f'[{get_curr_time()}] - [Thread {self.ID}] Saved image at "{output}/{enhanced_image_data[1]}.{enhanced_image_data[2]}"'
            )

            # Increment images enhanced counter of object
            self.enhanced_images += 1

        # Add the total of enhanced images of this object to the global total
        # Ensure mutual exclusion first
        num_images_enhanced_lock.acquire()
        num_images_enhanced += self.enhanced_images
        num_images_enhanced_lock.release()

        print(f"Thread {self.ID} is exiting...")
        
# Gets the current time (in seconds) of the program; for printing only
def get_curr_time():
    # Round off to two decimal places with trailing zeroes if needed
    return '{:.2f}'.format(round(time.perf_counter() - start_time, 2))

# Checks if time limit has been exceeded already
def check_time_exceeded(curr_time):
    # Global time system variables
    global start_time, time_limit

    # Convert time_limit to seconds
    return (curr_time - start_time) > (time_limit * 60.0)

# Enhances an image based on the brightness, sharpness, and contrast factors
def enhance_image(image_data):
    # Global image enhancement factors
    global brightness, sharpness, contrast

    # Get (open) image data using Pillow
    image = Image.open(f'{image_data[0]}/{image_data[1]}.{image_data[2]}')

    # Check if image is a gif
    if image_data[2].lower() == 'gif':
        # Initialize enhanced image
        enhanced = image
        
        # List of enhanced frames
        enhanced_frames = []

        # Enhance each frame of the gif
        for frame in ImageSequence.Iterator(image):
            # If time has already been exceeded, stop operation
            if check_time_exceeded(time.perf_counter()):
                return
            
            # Initialize enhanced frame by converting current frame's channel format to RGBA
            enhanced_frame = frame.convert('RGBA')

            # Enhance current frame based on enhancement factors using Pillow
            if (brightness != 1.0):
                # Modify brightness of image
                enhanced = ImageEnhance.Brightness(enhanced_frame).enhance(brightness)

            if (sharpness != 1.0):
                # Modify sharpness of image
                enhanced = ImageEnhance.Sharpness(enhanced_frame).enhance(sharpness)

            if (contrast != 1.0):
                # Modify contrast of image
                enhanced = ImageEnhance.Contrast(enhanced_frame).enhance(contrast)

            # Store enhanced current frame
            enhanced_frames.append(enhanced)

        # Append list of enhanced gif frames to image data
        image_data.append(enhanced_frames)
    else:
        # Initialize enhanced image
        enhanced = image
        
        if (brightness != 1.0):
            enhanced = ImageEnhance.Brightness(enhanced).enhance(brightness)

        if (sharpness != 1.0):
            enhanced = ImageEnhance.Sharpness(enhanced).enhance(sharpness)

        if (contrast != 1.0):
            enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)

        # Append enhanced image to image data
        image_data.append(enhanced)

    return image_data

# Gets all filenames of the images to be enhanced from the specified input folder path
def get_images(path):
    # Global image queue
    global images, num_images_input

    # Get the image filenames from the specified input folder
    for filename in os.listdir(path):
        # Check if it is an image file (jpg, png, or gif)
        if os.path.isfile(os.path.join(path, filename)) and filename.rsplit('.', 1)[1].lower() in formats:
            # Store input path, image filename, and extension (type / format) to image queue
            file_data = filename.rsplit('.', 1)
            images.put([path, file_data[0], file_data[1]])

    # Set the number of image inputs
    num_images_input = images.qsize()

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

    # Get all images from specified folder
    get_images(args.images)

    # If output folder in the given path does not yet exist, create the folder
    if not os.path.exists(output):
        os.makedirs(output)

    # Create threads based on given number of threads
    threads = []
    for i in range(num_threads):
        thread = ImageEnhancer(i+1)
        threads.append(thread)
        thread.start()

    # Join threads
    for thread in threads:
        thread.join()

    # Global number of images and number of enhanced images variables
    global num_images_input, num_images_enhanced

    # Global start time variable
    global start_time

    # Display statistics in the console
    finish_time = get_curr_time()
    print(f"\nTime elapsed: {finish_time} seconds")
    print(f"Brightness enhancement factor: {brightness}")
    print(f"Sharpness enhancement factor: {sharpness}")
    print(f"Contrast enhancement factor: {contrast}")
    print(f"Number of image enhancement threads used: {num_threads}")
    print(f"No. of input images: {num_images_input}")
    print(f"No. of enhanced images: {num_images_enhanced}\n")
    print(f"Enhanced images can be found in the {output} folder\n")

    # Create the statistics text file
    print(f"Creating statistics file...")
    file = open("stats.txt", "a")
    file.write(f"[TEST # {str(uuid.uuid4())}]\n")
    file.write(f"Time elapsed: {finish_time} seconds\n")
    file.write(f"Brightness enhancement factor: {brightness}\n")
    file.write(f"Sharpness enhancement factor: {sharpness}\n")
    file.write(f"Contrast enhancement factor: {contrast}\n")
    file.write(f"Number of image enhancement threads used: {num_threads}\n")
    file.write(f"No. of input images: {num_images_input}\n")
    file.write(f"No. of enhanced images: {num_images_enhanced}\n")
    file.write(f"Enhanced images can be found in the {output} folder\n\n")
    print(f"Statistics file created!")
    
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
