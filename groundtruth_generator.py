#!/usr/bin/python3
# Importing python3 from local, just use "python3 <binary>" if is not the same location

# /
# ** Luis ROSARIO, 2022
# ** label_2D_squares.py
# ** File description:
# ** Label 2D images with boxes
# ** https://github.com/Luisrosario2604
# */

# Imports
import argparse
import cv2
import os
import json


# Function declarations
def get_names_image(image_path):
    if not os.path.exists(image_path):
        raise Exception("\033[1m" + "[ERROR] -> File not existing" + "\033[0m")
    if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
        raise Exception("\033[1m" + "[ERROR] -> File is not an image" + "\033[0m")

    split = os.path.splitext(image_path)
    name = split[-2].split("/")[-1]
    image_ext = split[-1][1:]

    return name, image_ext


def get_roi(image):
    return cv2.selectROI(image)


def write_file(roi, image_path):
    name, _ = get_names_image(image_path)
    data = {
            'x': roi[0],
            'y': roi[1],
            'w': roi[2],
            'h': roi[3],
    }
    with open(os.path.join("groundtruth", name + ".json"), 'w') as outfile:
        json.dump(data, outfile)


def get_images(args):
    files_paths = []
    if args['file'] == "all":
        file_list = os.listdir('images')
        for file_path in file_list[:]:
            if file_path.endswith(".bmp"):
                files_paths.append('images/' + file_path)
    else:
        files_paths.append(args['file'])

    return files_paths


def get_arguments():
    ap = argparse.ArgumentParser()

    ap.add_argument("-f", "--file", required=True, help="path of the data file, ALL for all files")
    return vars(ap.parse_args())


def main():
    args = get_arguments()
    images_paths = get_images(args)

    for image_path in images_paths:
        image = cv2.imread(image_path)
        roi = get_roi(image)
        write_file(roi, image_path)


# Main body
if __name__ == '__main__':
    main()
