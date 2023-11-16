from dataclasses import dataclass
from sys import argv
from json import loads
from typing import List, Tuple
from rich.console import Console
from rich import print
from subprocess import run
import numpy as np

from util import *

import random

import cv2
console = Console()

@dataclass
class Box:
    p: List[Tuple[float, float]]    # top left, top right, bottom left, bottom right
    t: str

def get_richText_points(path: str) -> List[Box]:
    out = run(["./alexchan.swift", path], capture_output=True)
    return [Box(x['p'], x['t']) for x in loads(out.stdout)]

def read_img(path):
    return cv2.imread(path)

class Filters:
    @classmethod
    def alignment_is_square(cls, boxes: List[Box]):
        tol = 0.010 # can be 1.0% off of square in each corner
        def is_square(box):
            return abs(box.p[0][1] - box.p[1][1]) > tol  \
                or abs(box.p[1][0] - box.p[3][0]) > tol  \
                or abs(box.p[2][1] - box.p[3][1]) > tol  \
                or abs(box.p[0][0] - box.p[2][0]) > tol
            # return box.p[0][0] - box.p[1][0] > tol  \
            #     or box.p[1][1] - box.p[3][1] > tol  \
            #     or box.p[0][0] - box.p[2][0] > tol  \
            #     or box.p[2][1] - box.p[3][1] > tol
        return np.array([is_square(b) for b in boxes])

    @classmethod
    def away_from_border(cls, boxes: List[Box]):
        def is_border(box):
            if box.p[3][0] > 0.95:
                print(box.p[3][0])
            return any(p[0] == 0 or p[1] == 0 or p[0] == 1 or p[1] == 1 for p in box.p)
        return np.array([is_border(b) for b in boxes])

def main_annotate(img, boxes):
    thickness = 1
    # font variables from https://stackoverflow.com/a/34273603
    font      = cv2.FONT_HERSHEY_SIMPLEX
    lineType  = 2


    img = img.copy()
    coordify = lambda p: (int(p[0]*img.shape[1]), img.shape[0]-int(p[1]*img.shape[0]))

    filters = [
        Filters.alignment_is_square,
        Filters.away_from_border
    ]
    mask = np.any([f(boxes) for f in filters], axis=0)
    print(mask)

    color = '#326ccc'
    colors = np.array([color]*len(boxes))
    colors = np.ma.array(colors, mask=mask).filled('#ff0000')
    colors = [hex_to_rgb(c) for c in colors]


    for i, (box, color) in enumerate(zip(boxes, colors)):
        for i1, i2 in [(0, 1), (1, 3), (0, 2), (2, 3)]:
            cv2.line(img, coordify(box.p[i1]), coordify(box.p[i2]), color, thickness, lineType=cv2.LINE_AA)

        cv2.putText(img, f"{i}", coordify(box.p[2]), font, 0.02 * abs(coordify(box.p[0])[1] - coordify(box.p[2])[1]), color, 3, lineType)

    cv2.imshow('pictoor', img)
    cv2.waitKey(0)

def main():
    # points: List[Box] = loads(argv[1])
    # console.print(points)

    impath = argv[1]
    boxes = get_richText_points(impath)
    img = read_img(impath)
    main_annotate(img, boxes)

if __name__ == '__main__':
    main()


