from dataclasses import dataclass
from sys import argv
from json import loads
from typing import List, Tuple
from rich.console import Console
from rich import print
from subprocess import run
import numpy as np
from operator import itemgetter as ig, attrgetter as ag, methodcaller as mc
from functools import partial, cached_property
from matplotlib import pyplot as plt
from macropy.quick_lambda import macros, f, _

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
    im_dims: Tuple[int, int]

    @classmethod
    def from_pt(cls, img, p, t):
        (x1, y1), (x2, y2) = coordify(img, p[0]), coordify(img, p[3])
        (x3, y3), (x4, y4) = coordify(img, p[0]), coordify(img, p[3])
        x1, x2 = min(x1, x2, x3, x4), max(x1, x2, x3, x4)
        y1, y2 = min(y1, y2, y3, y4), max(y1, y2, y3, y4)
        return Box(p, t, img[y1:y2, x1:x2], img.shape[:2])

    @classmethod
    def from_corners(cls, img: np.ndarray, p1, p2, t):
        return Box.from_pt(img, [p1, (p2[0], p1[1]), (p1[0], p2[1]), p2], t)

    @cached_property
    def fg_bg_colors(self) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int]]]:
        """returns in BGR to match opencv"""
        n_samples = 100
        # n_samples = max(self.w_px * self.h_px//10, 50)    # TODO: put back
        rng = np.random.default_rng()
        # print(self.i, np.vstack(self.i).shape, 'cow')
        sample = rng.choice(np.vstack(self.i), size=n_samples)  # TODO: from last time. was making a random-sample thing and then ig just histogram/counting sort to find the bg color and fg color? or could do max distance of unifrom color or smt, bc fonts are usually stroke-based while the area between is usually larger

        # colors = [bgr_to_hex(pix) for pix in sample]
        # sample = np.apply_along_axis(bgr_to_hsv, 1, sample)
        # fig = plt.figure()
        # ax = fig.add_subplot(211, projection='3d')
        # img_ax = fig.add_subplot(212)
        # img_ax.imshow(self.i)
        # img_ax.set_title(self.t)
        # ax.scatter(*sample.T, c=colors)
        # ax.set_xlabel('v')
        # ax.set_ylabel('s')
        # ax.set_zlabel('h')
        # plt.show()
        # print(sample)

        fgs = []
        bgs = []
        return [], []

    @cached_property
    def est_font_size(self) -> float:
        return self.h

    @property
    def tl(self): return self.p[0]
    @property
    def tr(self): return self.p[1]
    @property
    def bl(self): return self.p[2]
    @property
    def br(self): return self.p[3]
    @property
    def x(self): return self.p[0][0]
    @property
    def y(self): return self.p[0][1]
    @property
    def w(self): return abs(self.br[0] - self.bl[0])
    @property
    def h(self): return abs(self.br[1] - self.bl[1])
    @property
    def x_px(self): return int(self.p[0][0] * self.im_w)
    @property
    def y_px(self): return int(self.p[0][1] * self.im_h)
    @property
    def w_px(self): return int(abs(self.br[0] - self.bl[0]) * self.im_w)
    @property
    def h_px(self): return int(abs(self.br[1] - self.bl[1]) * self.im_h)
    @property
    def im_w(self): return self.im_dims[0]
    @property
    def im_h(self): return self.im_dims[1]

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
        color = hex_to_bgr(color) if type(color) is str else color

        for i1, i2 in [(0, 1), (1, 3), (0, 2), (2, 3)]:
            cv2.line(img, cify(box.p[i1]), cify(box.p[i2]), color, thickness, lineType=cv2.LINE_AA)

        # for i1, i2 in [(0, 1), (2, 3)]: # just draw the x ones
        #     cv2.line(img, cify(box.p[i1]), cify(box.p[i2]), hex_to_rgb('#00ff00'), thickness, lineType=cv2.LINE_AA)

        cv2.putText(img, f"{i}", cify(box.p[2]), font, 0.02 * abs(cify(box.p[0])[1] - cify(box.p[2])[1]), color, 3, lineType)

def filter_boxes_with(boxes, *filters, img: np.ndarray=None, color: str=None, label: str=None) -> List[Box]:
    mask = np.all([f(boxes) for f in filters], axis=0)
    masked_out = np.ma.array(boxes, mask=mask).compressed()
    if img is not None:
        if color is None: color = '#ff0000'
        if label is None: label = 'masked out'
        draw_boxes(img, masked_out, color, label)
    return np.ma.array(boxes, mask=~mask).compressed()

def main_annotate(img, boxes):
    img = img.copy()

    #### pre filtering
    # filter_boxes_with(boxes, Filters.alignment_is_square)


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
    p_boxes = filter_boxes_with(p_boxes, Filters.away_from_border, img=img, label='edgy')


    # draw_boxes(img, boxes, '#007700', 'correct')

    fig, ax = plt.subplots()
    ax.hist([b.est_font_size for b in boxes], bins=100)
    plt.show()

    cv2.imshow('pictoor', img)
    cv2.waitKey(0)

def main():
    # points: List[Box] = loads(argv[1])

    impath = argv[1]
    boxes = get_richText_points(impath)
    for box in boxes:
        print(box.fg_bg_colors)
    img = read_img(impath)
    main_annotate(img, boxes)

if __name__ == '__main__':
    main()


