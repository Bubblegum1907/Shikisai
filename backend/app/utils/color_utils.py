import math

def hex_to_rgb(hex_code: str):
    """Converts #RRGGBB to (R, G, B) tuple."""
    hex_code = hex_code.lstrip('#')
    if len(hex_code) != 6:
        return (128, 128, 128) # Fallback gray
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_xyz(rgb):
    """Converts RGB to XYZ color space."""
    def pivot(n):
        n /= 255
        return ((n + 0.055) / 1.055) ** 2.4 if n > 0.04045 else n / 12.92

    r, g, b = map(pivot, rgb)
    
    # Observer. = 2°, Illuminant = D65
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    return x, y, z

def xyz_to_lab(xyz):
    """Converts XYZ to CIELAB."""
    x, y, z = xyz
    # Reference white D65
    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    def pivot(n):
        return n ** (1/3) if n > 0.008856 else (7.787 * n) + (16 / 116)

    fx, fy, fz = map(pivot, (x, y, z))
    l = (116 * fy) - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return l, a, b

def hex_to_lab(hex_code: str):
    """The master function used by palette_loader."""
    try:
        rgb = hex_to_rgb(hex_code)
        xyz = rgb_to_xyz(rgb)
        return xyz_to_lab(xyz)
    except Exception:
        return (50.0, 0.0, 0.0) # Neutral gray fallback