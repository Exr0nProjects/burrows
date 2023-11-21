import numpy as np
from colorsys import rgb_to_hsv, hsv_to_rgb

def hex_to_bgr(hex_color: str):
    hex_color = hex_color.strip()
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    assert len(hex_color) == 6
    return list(reversed([int(hex_color[i:i+2], base=16) for i in range(0, 5, 2)]))

def bgr_to_hex(bgr: np.ndarray):
    return '#' + ''.join(f"{n:02x}" for n in reversed(bgr))

def bgr_to_hsv(bgr: np.ndarray):
    return rgb_to_hsv(*reversed(bgr))