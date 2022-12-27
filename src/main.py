#!/usr/bin/python3
# Importing python3 from local, just use "python3 <binary>" if is not the same location

# /
# ** Luis ROSARIO, 2021
# ** main.py
# ** File description:
# ** Segmentación precisa de la imagen de la oreja
# ** https://github.com/Luisrosario2604
# */


# https://scipy-lectures.org/packages/scikit-image/auto_examples/plot_labels.html

# Imports
import argparse
import numpy as np
import cv2
import scipy.ndimage
import os
import json
from shapely.geometry import Polygon


# Function declarations
def open_image(file_name):
    img = cv2.imread(file_name)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def get_images(args):
    file_names = []
    if args['file'] == "all":
        file_list = os.listdir('data')
        for file_name in file_list[:]:
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                file_names.append('data/' + file_name)
    else:
        if not os.path.exists(args['file']):
            raise Exception("\033[1m" + "[ERROR] -> File not existing" + "\033[0m")
        if not args['file'].lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            raise Exception("\033[1m" + "[ERROR] -> File is not an image" + "\033[0m")
        file_names.append(args['file'])

    return file_names


# Not my function -> getting kernel used in top-hat
def estructurant(radius):
    kernel = np.zeros((2 * radius + 1, 2 * radius + 1), np.uint8)
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    mask = x ** 2 + y ** 2 <= radius ** 2
    kernel[mask] = 1
    kernel[0, radius-1:kernel.shape[1]-radius+1] = 1
    kernel[kernel.shape[0] - 1, radius - 1:kernel.shape[1] - radius + 1] = 1
    kernel[radius - 1:kernel.shape[0]-radius + 1, 0] = 1
    kernel[radius - 1:kernel.shape[0]-radius + 1, kernel.shape[1]-1] = 1
    return kernel


def get_names_image(image_path):
    split = os.path.splitext(image_path)
    name = split[-2].split("/")[-1]
    image_ext = split[-1][1:]

    return name, image_ext


def get_ground_truth_roi(file_name):
    name, _ = get_names_image(file_name)
    with open("./groundtruth/" + name + ".json") as f:
        data = json.load(f)
    return [data['x'], data['y'], data['w'], data['h']]


# Getting the kernel to be used in Top-Hat
# Applying the Top-Hat operation (different then black-hat)
def top_hat(img, kernel_size, kernel_choice=1):

    if kernel_choice == 1:
        kernel = estructurant(kernel_size)
    else:
        filter_size = (kernel_size, kernel_size)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, filter_size)

    return cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)


def getBlackAndWhite(blackhat_img):
    _, thresh_result = cv2.threshold(blackhat_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh_result


def get_largest_component(image):
    s = scipy.ndimage.generate_binary_structure(2, 1)
    labeled_array, numpatches = scipy.ndimage.label(image, s)
    sizes = scipy.ndimage.sum(image, labeled_array, range(1, numpatches + 1))
    max_label = np.where(sizes == sizes.max())[0] + 1
    biggest_stain = np.asarray(labeled_array == max_label, np.uint8)
    biggest_stain[biggest_stain > 0] = 255
    return biggest_stain


def drawContourAndShowImage(biggest_stain, default_image):
    contours, hierarchy = cv2.findContours(biggest_stain, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    (x, y, w, h) = cv2.boundingRect(contours[0])

    size = default_image.shape

    if h >= 260:
        h = int(h - h // 5)
    elif y > 20 and y + h + 20 <= size[0]:
        y -= 20
        h += 40

    if w >= 300:
        x += int(w // 7)
        w = w - w // 5
    elif x > 20 and x + w + 20 <= size[1]:
        w += 40
        x -= 20

    square_contour_img = cv2.cvtColor(default_image.copy(), cv2.COLOR_GRAY2RGB)

    square_contour_img = cv2.rectangle(square_contour_img, (x, y), (x + w, y + h), (47, 61, 226), 4)

    return square_contour_img, [x, y, w, h]


def draw_groundtruth(square_contour_img, roi, gt_roi, show):

    if show in ["groundtruth", "detail"]:
        square_contour_img = cv2.rectangle(square_contour_img, (gt_roi[0], gt_roi[1]), (gt_roi[0] + gt_roi[2], gt_roi[1] + gt_roi[3]), (78, 255, 97), 1)

    x = roi[0]
    y = roi[1]
    w = roi[2]
    h = roi[3]

    x2 = gt_roi[0]
    y2 = gt_roi[1]
    w2 = gt_roi[2]
    h2 = gt_roi[3]

    box_1 = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
    box_2 = [[x2, y2], [x2 + w2, y2], [x2 + w2, y2 + h2], [x2, y2 + h2]]

    poly_1 = Polygon(box_1)
    poly_2 = Polygon(box_2)
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area

    if show in ["confidence", "groundtruth", "detail"]:
        square_contour_img = cv2.putText(square_contour_img, "IOU = " + str(round(iou, 3)), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (47, 61, 226), 2, cv2.LINE_AA)

    return square_contour_img


def show_result(kernel_size, tophat_img, black_and_white, biggest_stain, square_contour_img, show):
    window_name = "File : " + str(kernel_size)
    cv2.namedWindow(window_name)
    cv2.moveWindow(window_name, 0, 30)

    if show in ["detail"]:
        tmp_1 = cv2.hconcat((cv2.cvtColor(tophat_img, cv2.COLOR_GRAY2RGB), cv2.cvtColor(black_and_white, cv2.COLOR_GRAY2RGB)))
        tmp_2 = cv2.hconcat((cv2.cvtColor(biggest_stain, cv2.COLOR_GRAY2RGB), square_contour_img))
        final_img = cv2.vconcat((tmp_1, tmp_2))
        cv2.imshow(window_name, final_img)
    else:
        cv2.imshow(window_name, square_contour_img)

    cv2.waitKey()
    cv2.destroyAllWindows()


def get_arguments():
    ap = argparse.ArgumentParser()

    ap.add_argument("-f", "--file", required=True, help="path of the data file")
    ap.add_argument("-s", "--show", required=False, help="what image will be display : \"result\" - \"confidence\" - \"groundtruth\" - \"detail\"", default="result")
    return vars(ap.parse_args())


def main():
    args = get_arguments()
    if args["show"] not in ["result", "confidence", "groundtruth", "detail"]:
        raise Exception("\033[1m" + "[ERROR] -> Show parameter is not good, should be : result, confidence, groundtruth or detail" + "\033[0m")
    file_names = get_images(args)
    kernel_size = 53    # 41, 53 working fine

    for file_name in file_names:
        image = open_image(file_name)
        tophat_img = top_hat(image, kernel_size)
        black_and_white = getBlackAndWhite(tophat_img)

        biggest_stain = get_largest_component(black_and_white)

        square_contour_img, roi = drawContourAndShowImage(biggest_stain, image)

        gt_roi = get_ground_truth_roi(file_name)
        square_contour_img = draw_groundtruth(square_contour_img, roi, gt_roi, args["show"])

        show_result(kernel_size, tophat_img, black_and_white, biggest_stain, square_contour_img, args["show"])


# Main body
if __name__ == '__main__':
    main()
