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

# Process synchronization libraries
import multiprocessing  # For creating processes
from queue import Empty # Exception to determine if queue is already empty
import time             # For time checking, etc.

# Constant global variables
formats = ['jpg', 'png', 'gif'] # Accepted image types / formats

# ImageEnhancer process class, responsible for performing the image enhancing operations
class ImageEnhancer(multiprocessing.Process):
    # Constructor 
    def __init__(self, processID, brightness, sharpness, contrast,
                 output, images, num_enhanced_global, num_enhanced_global_lock, 
                 time_limit, start_time):
        multiprocessing.Process.__init__(self)
        self.ID = processID
        self.num_enhanced = 0
        self.brightness = brightness
        self.sharpness = sharpness
        self.contrast = contrast
        self.output = output
        self.images = images
        self.num_enhanced_global = num_enhanced_global
        self.num_enhanced_global_lock = num_enhanced_global_lock
        self.time_limit = time_limit
        self.start_time = start_time
        
    # Instructions the the ImageEnhancer process will do once it runs
    def run(self):
        print(f"Process {self.ID} is starting...")
        
        # Repeat until no more images to be enhanced
        while self.images.empty() is not True:
            # If time limit exceeded, break the loop
            if check_time_exceeded(self.start_time, self.time_limit, time.perf_counter()):
                break
            
            # Gets the data of an image from the queue
            # Stop operation after 2 seconds since it is possible that there are no more images in the queue
            try:
                curr_image_data = self.images.get(timeout = 2)
            except Empty:
                break
            
            # Enhance the image
            enhanced_image_data = enhance_image(curr_image_data, self.brightness, self.sharpness, self.contrast, self.start_time, self.time_limit)
            
            # Get current time in seconds after image enhancement (for printing)
            print(f"[{get_curr_time(self.start_time)}] - [Process {self.ID}] Enhancing {curr_image_data[1]}.{curr_image_data[2]}")
            
            # Save the enhanced image to the output folder
            # If current image is a gif
            if enhanced_image_data[2].lower() == 'gif':
                # Save gif frames, start from first frame
                enhanced_image_data[3][0].save(
                    f'{self.output}/{enhanced_image_data[1]}.{enhanced_image_data[2]}',
                    save_all=True,
                    # append rest of the frames, starting from second frame
                    append_images=enhanced_image_data[3][1:],
                    duration=100,
                    loop=0
                )
            else:
                # Save image (jpg or png)
                enhanced_image_data[3].save(f'{self.output}/{enhanced_image_data[1]}.{enhanced_image_data[2]}')
                
            # Get current time in seconds after saving enhanced image (for printing)
            print(
                f'[{get_curr_time(self.start_time)}] - [Process {self.ID}] Saved image at "{self.output}/{enhanced_image_data[1]}.{enhanced_image_data[2]}"'
            )
            
            # Increment images enhanced counter of object
            self.num_enhanced += 1
            
        # Add the total of enhanced images of this object to the shared total
        # Ensure mutual exclusion first
        self.num_enhanced_global_lock.acquire()
        self.num_enhanced_global.value += self.num_enhanced
        self.num_enhanced_global_lock.release()
        
        print(f"Process {self.ID} is exiting...")

# Gets the current time (in seconds) of the program; for printing only
def get_curr_time(start_time):
    # Round off to two decimal places with trailing zeroes if needed
    return '{:.2f}'.format(round(time.perf_counter() - start_time, 2))

# Checks if the time limit has been exceeded already
def check_time_exceeded(start_time, time_limit, curr_time):
    # Convert time_limit to seconds
    return (curr_time - start_time) > (time_limit * 60.0)

# Enhances an image based on the brightness, sharpness, and contrast factors
def enhance_image(image_data, brightness, sharpness, contrast, 
                  start_time, time_limit):
    # Get (open) image data using Pillow
    image = Image.open(f'{image_data[0]}/{image_data[1]}.{image_data[2]}')

    # Check if image is a gif
    if image_data[2].lower() == 'gif':
        # Initialize enhanced image
        enhanced = image

        # List of enhanced frames
        enhanced_frames = []

        # Enhance each frame of the gif
        for frame in ImageSequence.Iterator(enhanced):
            # Initialize enhanced frame by converting current frame's channel format to RGBA
            enhanced_frame = frame.convert('RGBA')

            # Enhance current frame based on enhancement factors using Pillow
            if (brightness != 1.0):
                # Modify brightness of image
                enhanced_frame = ImageEnhance.Brightness(
                    enhanced_frame).enhance(brightness)

            if (sharpness != 1.0):
                # Modify sharpness of image
                enhanced_frame = ImageEnhance.Sharpness(
                    enhanced_frame).enhance(sharpness)

            if (contrast != 1.0):
                # Modify contrast of image
                enhanced_frame = ImageEnhance.Contrast(
                    enhanced_frame).enhance(contrast)

            # Store enhanced current frame
            enhanced_frames.append(enhanced_frame)

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
def get_images(path, images):
    # Get the image filenames from the specified input folder
    for filename in os.listdir(path):
        # Check if it is an image file (jpg, png, or gif)
        if os.path.isfile(os.path.join(path, filename)) and filename.rsplit('.', 1)[1].lower() in formats:
            # Store input path, image filename, and extension (type / format) to image queue
            file_data = filename.rsplit('.', 1)
            images.put([path, file_data[0], file_data[1]])
            
# Main function
def main(args):
    # Initialize system variables
    time_limit = fabs(args.time)
    num_processes = abs(args.processes)
    brightness = fabs(args.brightness)
    sharpness = fabs(args.sharpness)
    contrast = fabs(args.contrast)
    output = args.output
    start_time = time.perf_counter() # Time the program has started its execution
    
    # Initialize multiprocessing variables
    manager = multiprocessing.Manager() # For creating process-shared variables
    num_enhanced_global = manager.Value('num_enhanced_global', 0) # Number of images enhanced
    num_enhanced_global_lock = multiprocessing.Lock() # For updating the shared num_enhanced_global variable
    images = multiprocessing.Queue() # Images queue
    
    # Get all images from specified folder
    get_images(args.images, images)
    
    # Set the number of image inputs
    num_images_input = images.qsize()
    
    # If output folder in the given path does not yet exist, create the folder
    if not os.path.exists(output):
        os.makedirs(output) 
        
    # Create processes based on given number of processes
    processes = []
    for i in range(num_processes):
        process = ImageEnhancer(i+1, brightness, sharpness, contrast,
                                output, images, num_enhanced_global, 
                                num_enhanced_global_lock, time_limit, 
                                start_time)
        processes.append(process)
        process.start()
        
    # Join processes
    for process in processes:
        process.join()
        
    # Empty queue if there are still images not enhanced
    # This is to avoid blocking the main process from terminating
    while not images.empty():
        images.get()
        
    # Get finish time of program
    finish_time = get_curr_time(start_time)
    # Get unique ID for this run
    UUID = str(uuid.uuid4())

    # Display statistics in the console
    print(f"[TEST ID: {UUID}]")
    print(f"\nTime elapsed: {finish_time} seconds")
    print(f"Brightness enhancement factor: {brightness}")
    print(f"Sharpness enhancement factor: {sharpness}")
    print(f"Contrast enhancement factor: {contrast}")
    print(f"Number of image enhancement processes used: {num_processes}")
    print(f"No. of input images: {num_images_input}")
    print(f"No. of enhanced images: {num_enhanced_global.value}\n")
    print(f"Enhanced images can be found in the {output} folder\n")

    # Create the statistics text file
    print(f"Creating statistics file...")
    file = open("stats-process.txt", "a")
    file.write(f"[TEST ID: {UUID}]")
    file.write(f"\nTime elapsed: {finish_time} seconds\n")
    file.write(f"Brightness enhancement factor: {brightness}\n")
    file.write(f"Sharpness enhancement factor: {sharpness}\n")
    file.write(f"Contrast enhancement factor: {contrast}\n")
    file.write(f"Number of image enhancement processes used: {num_processes}\n")
    file.write(f"No. of input images: {num_images_input}\n")
    file.write(f"No. of enhanced images: {num_enhanced_global.value}\n")
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
    parser.add_argument('-n', '--processes',
                        type=int,
                        help='Number of processes to use, converted to absolute value',
                        default=5,
                        required=False)

    args = parser.parse_args()
    
    # Begin program
    main(args)
