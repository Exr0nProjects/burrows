from typing import List, Tuple
import numpy as np
import cv2
import tesseract_helper
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

def estimate_aspect_ratio(points: List[Tuple[int, int]]):
    """from https://pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/"""
    # obtain a consistent order of the points and unpack them
    # individually
    (tl, tr, bl, br) = points
    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [0, maxHeight - 1],
            [maxWidth - 1, maxHeight - 1],
        ], dtype = "float32")
    return maxWidth, maxHeight, dst

def four_point_transform(image, points: List[Tuple[int, int]]):
    # compute the perspective transform matrix and then apply it
    maxWidth, maxHeight, dst = estimate_aspect_ratio(points)
    M = cv2.getPerspectiveTransform(points, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    # return the warped image
    return warped

def warp_and_tessaract_correct(image, points: List[Tuple[int, int]]):
    maxWidth, maxHeight, dst = estimate_aspect_ratio(points)

    # transform into rectified space
    M = cv2.getPerspectiveTransform(points, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))


    # use tessaract to find a tighter bounding box
    words = list(tesseract_helper.get_flattened_words(warped))

    # logging
    # fig, ax = plt.subplots()
    # ax.imshow(warped)
    # for w in words:
    #     ax.add_patch(Rectangle((w.left, w.top), w.width, w.height, fill=False))

    # plt.show()
    # print(words)

    if len(words) == 0: return warped, points, maxHeight * 0.8
    avg_height = sum(w.height for w in words)/len(words)

    x1 = min(w.left for w in words)
    x2 = max(w.left + w.width for w in words)
    y1 = min(w.top for w in words)
    y2 = max(w.top + w.height for w in words)

    tightened_img = warped[x1:x2, y1:y2]


    # transform tighter bounding box back into image space
    M_inv = np.linalg.pinv(M)
    packed_rectified_tightened_points = np.array([[(x1, y1), (x2, y1), (x1, y2), (x2, y2)]], dtype='float32')
    og_space = cv2.perspectiveTransform(packed_rectified_tightened_points, M_inv)

    return tightened_img, og_space, avg_height


