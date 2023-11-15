import argparse
import sys
import io
from operator import itemgetter as ig, attrgetter as ag, methodcaller as mc

# from PIL import Image
import cv2
import numpy as np
import pytesseract
import pandas as pd



def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bytes", type=bytes, help="utf-8 encoded string of the png file to parse, or - to read from stdin")
    args = parser.parse_args()

    if args.bytes:
        img_bytes = args.bytes
    else:
        img_bytes = sys.stdin.buffer.read()

    img_bytes = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    # return Image.open(io.BytesIO(img_bytes))

def main():
    image = parse_args()
    ocr_data: pd.DataFrame = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
    # ocr_data = ocr_data[ocr_data['conf'] > 0]


    # algorithmics todo:
    #   cluster the sampled background/foreground colors
    #   find repeated spatial structures?

    # print(ocr_data)
    print_lines(ocr_data)
    annotate_image(image, ocr_data)

def print_lines(ocr_data):
    rolling_linebuf = []
    rolling_prev_level = 0
    for i, (level, line_num, conf, text) in ocr_data[['level', 'line_num', 'conf', 'text']].iterrows():
        if (level != rolling_prev_level):
            print(' '.join(rolling_linebuf))
            rolling_linebuf = []
        rolling_prev_level = level
        if (level == 5): rolling_linebuf.append(text.strip())
    print(' '.join(rolling_linebuf))


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.strip()
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    assert len(hex_color) == 6
    return list(reversed([int(hex_color[i:i+2], base=16) for i in range(0, 5, 2)]))








def annotate_image(img, ocr_data):
    annotated = img.copy()

    """
    > level:
    > 1. a page
    > 2. a block
    > 3. a paragraph
    > 4. a line
    > 5. a word.
    Looks like block detection is pretty good for headings, but it may split non-headings (esp. code / very varied line lengths into headings)
    very much struggles for UIs

    i probably need to detect the main body and then re-run on just that
    """
    print(hex_to_rgb('#326ccc'))
    for i, (level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text) in ocr_data.iterrows():
        start_point =(left, top)
        end_point =(left + width, top + height)

        if level == 5:  # annotate words
            cv2.rectangle(annotated, start_point, end_point, (0, 0, 255), thickness=1, lineType=cv2.LINE_8)

        if level == 4:  # annotate lines
            cv2.rectangle(annotated, start_point, end_point, hex_to_rgb('#326ccc'), thickness=1, lineType=cv2.LINE_8)

        if level == 2:
            cv2.rectangle(annotated, start_point, end_point, (0, 200, 0), thickness=1, lineType=cv2.LINE_8)

    cv2.imshow('annotated', annotated)
    cv2.waitKey(0)
    cv2.imwrite('./examples/' + 'woof.png', annotated)



if __name__ == '__main__':
    # eg usage: brew install pngpaste; pngpaste - | py main.py
    main()
