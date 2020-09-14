# Bitmapy
Python module for reading and writing bitmaps

## Usage

```
from bitmapy import Bitmap

lighten = lambda color : color + 20 if color + 20 < 255 else 255

bmp = Bitmap('original.bmp')
for px in bmp.enumerate_pixels():
    b, g, r = px.pixel_data()
    lighter_rgb = (lighten(b), lighten(g), lighten(r))
    px.update_pixel_data(lighter_rgb)

bmp.save_as("copy.bmp")
```
