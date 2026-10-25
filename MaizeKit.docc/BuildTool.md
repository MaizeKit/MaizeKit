# Build Tool

How `tools/build_assets.py` turns a photo into a map.

```
Builds the georeferenced maze overlay and routing grid from a photo of the maze map.

The sign is warped (homography) onto the real field outline, so every output is a
north-up raster: pixel (x, y) -> east = x * RES, north = -y * RES from ORIGIN.

Usage: python tools/build_assets.py [maze.config.json]
Needs: opencv-python-headless, numpy
```

[View the source](https://github.com/MaizeKit/maizekit/blob/main/tools/build_assets.py)
