# Getting Started

Make a site for your maze in six steps.

1. Click **Use this template** to create a repo for your maze, e.g. `my-farm`.
2. Add a straight-on photo of the maze map as `sign-photo.png`.
3. Copy `maze.config.example.json` to `maze.config.json` and fill it in ([see below](#configuration)).
4. Build the map:
   ```sh
   pip install opencv-python-headless numpy
   python tools/build_assets.py
   ```
   This writes the `assets/` folder. Open `assets/maze.webp` to check it.
5. Set the app's name in `manifest.webmanifest`.
6. Commit and push, then turn on **GitHub Pages** (Settings › Pages › branch `main`, folder `/`).


## Entrance sign


Open `sign.html` on your published site and print it. It has a QR code for the site's
own address, so it's always right for your maze.
