import argparse
import sys
import io

from PIL import Image




def parse_args() -> Image:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bytes", type=bytes, help="utf-8 encoded string of the png file to parse, or - to read from stdin")
    args = parser.parse_args()

    if args.bytes:
        img_bytes = args.bytes
    else:
        img_bytes = sys.stdin.buffer.read()

    return Image.open(io.BytesIO(img_bytes))

def main():
    got = parse_args()
    got.show()
    print(got)


if __name__ == '__main__':
    # eg usage: brew install pngpaste; pngpaste - | py main.py
    main()
