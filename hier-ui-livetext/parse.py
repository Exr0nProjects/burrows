from dataclasses import dataclass
from sys import argv
from json import loads
from typing import List, Tuple
from rich.console import Console
from rich import print
from subprocess import run
import numpy as np
from operator import itemgetter as ig, attrgetter as ag, methodcaller as mc
from functools import partial

from util import *

import random

import cv2
console = Console()

coordify = lambda img, p: (int(p[0]*img.shape[1]), img.shape[0]-int(p[1]*img.shape[0]))

@dataclass
class Box:
    p: List[Tuple[float, float]]    # top left, top right, bottom left, bottom right
    t: str
    i: np.ndarray

    @classmethod
    def from_pt(cls, img, p, t):
        (x1, y1), (x2, y2) = coordify(img, p[0]), coordify(img, p[3])
        return Box(p, t, img[x1:x2, y1:y2])

    @classmethod
    def from_corners(cls, img: np.ndarray, p1, p2, t):
        return Box.from_pt(img, [p1, (p2[0], p1[1]), (p1[0], p2[1]), p2], t)

def read_img(path):
    return cv2.imread(path)

def get_richText_points(path: str) -> List[Box]:
    out = run(["./alexchan.swift", path], capture_output=True)
    img = read_img(path)
    return [Box.from_pt(img, **x) for x in loads(out.stdout)]

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


    cify = partial(coordify, img)
    for i, (box, color) in enumerate(zip(boxes, colors)):
        color = hex_to_rgb(color) if type(color) is str else color

        for i1, i2 in [(0, 1), (1, 3), (0, 2), (2, 3)]:
            cv2.line(img, cify(box.p[i1]), cify(box.p[i2]), color, thickness, lineType=cv2.LINE_AA)

        # for i1, i2 in [(0, 1), (2, 3)]: # just draw the x ones
        #     cv2.line(img, cify(box.p[i1]), cify(box.p[i2]), hex_to_rgb('#00ff00'), thickness, lineType=cv2.LINE_AA)

        cv2.putText(img, f"{i}", cify(box.p[2]), font, 0.02 * abs(cify(box.p[0])[1] - cify(box.p[2])[1]), color, 3, lineType)


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
    para_texts = []
    prev = None
    for box in boxes:
        if prev is None or prev.p[0][1] < box.p[3][1]:
            paragraphs.append([])
            para_texts.append("")
        paragraphs[-1].append(box)
        para_texts[-1] += ' ' + box.t
        prev = box

    def calc_bounds(boxes):
        flatten = lambda ll: [x for y in ll for x in y]
        xs = flatten([[b.p[0][0], b.p[3][0]] for b in boxes])
        ys = flatten([[b.p[0][1], b.p[3][1]] for b in boxes])
        return [(np.min(xs), np.max(ys)), (np.max(xs), np.min(ys))]
    paragraph_bounds = [calc_bounds(bs) for bs in paragraphs]
    p_boxes = [Box.from_corners(img, p1, p2, t) for (p1, p2), t in zip(paragraph_bounds, para_texts)]
    draw_boxes(img, p_boxes, colors="#00ff00")


    ### remove things on the edge
    mask = Filters.away_from_border(p_boxes)
    edgy = np.ma.array(p_boxes, mask=mask).compressed()
    draw_boxes(img, edgy, '#ff0000', 'edgy')


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


