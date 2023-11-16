def hex_to_rgb(hex_color: str):
    hex_color = hex_color.strip()
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    assert len(hex_color) == 6
    return list(reversed([int(hex_color[i:i+2], base=16) for i in range(0, 5, 2)]))