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
            return abs(box.p[0][1] - box.p[1][1]) < tol  \
               and abs(box.p[1][0] - box.p[3][0]) < tol  \
               and abs(box.p[2][1] - box.p[3][1]) < tol  \
               and abs(box.p[0][0] - box.p[2][0]) < tol
        return np.array([is_square(b) for b in boxes])

    @classmethod
    def away_from_border(cls, boxes: List[Box]):
        def is_border(box):
            thresh = 0.01   # within 1% of the edge
            # only consider top left and bottom right
            top = box.p[0][1]
            bot = box.p[3][1]
            lef = box.p[0][0]
            rig = box.p[3][0]

            if top < thresh or bot > 1-thresh: return False
            if lef < thresh or rig > 1-thresh: return False
            return True
            # TODO: somehow check if it looks like a cut-off word.
        return np.array([is_border(b) for b in boxes])

def draw_boxes(img, boxes, colors, labels=None):
    thickness = 1
    # font variables from https://stackoverflow.com/a/34273603
    font      = cv2.FONT_HERSHEY_SIMPLEX
    lineType  = 2

    if labels is None: labels = [""] * len(boxes)
    if type(labels) is str: labels = [labels] * len(boxes)
    else: assert len(labels) == len(boxes)

    if type(colors) is str: colors = [colors] * len(boxes)
    else: assert len(colors) == len(boxes)

    coordify = lambda p: (int(p[0]*img.shape[1]), img.shape[0]-int(p[1]*img.shape[0]))

    for i, (box, color) in enumerate(zip(boxes, colors)):
        color = hex_to_rgb(color) if type(color) is str else color

        for i1, i2 in [(0, 1), (1, 3), (0, 2), (2, 3)]:
            cv2.line(img, coordify(box.p[i1]), coordify(box.p[i2]), color, thickness, lineType=cv2.LINE_AA)

        # for i1, i2 in [(0, 1), (2, 3)]: # just draw the x ones
        #     cv2.line(img, coordify(box.p[i1]), coordify(box.p[i2]), hex_to_rgb('#00ff00'), thickness, lineType=cv2.LINE_AA)

        cv2.putText(img, f"{i}", coordify(box.p[2]), font, 0.02 * abs(coordify(box.p[0])[1] - coordify(box.p[2])[1]), color, 3, lineType)


def main_annotate(img, boxes):
    img = img.copy()

    #### pre filtering
    filters = [
        Filters.alignment_is_square,
    ]
    mask = np.all([f(boxes) for f in filters], axis=0)
    not_aligned = np.ma.array(boxes, mask=mask).compressed()
    draw_boxes(img, not_aligned, '#ff0000', 'misaligned')

    boxes = np.ma.array(boxes, mask=~mask).compressed()


    ### chunking into paragraphs
    paragraphs = []
    prev = None
    for box in boxes:
        if prev is None or prev.p[0][1] < box.p[3][1]:
            paragraphs.append([])
        paragraphs[-1].append(box)
        prev = box

    def calc_bounds(boxes):
        flatten = lambda ll: [x for y in ll for x in y]
        xs = flatten([[b.p[0][0], b.p[3][0]] for b in boxes])
        ys = flatten([[b.p[0][1], b.p[3][1]] for b in boxes])
        return [(np.min(xs), np.max(ys)), (np.max(xs), np.min(ys))]
    paragraph_bounds = [calc_bounds(bs) for bs in paragraphs]
    draw_boxes(img, [Box([p1, (p2[0], p1[1]), (p1[0], p2[1]), p2 ], "_") for p1, p2 in paragraph_bounds], colors="#00ff00")
    draw_boxes(img, boxes, '#007700', 'correct')

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


