<div align="center">

<img src="brand/maizekit-icon-256.png" width="112" height="112" alt="MaizeKit icon">

# MaizeKit

**Turn a photo of a corn maze map into a phone app that shows where you are and the way out.**

[![Built with MaizeKit](brand/badge/built-with-maizekit.svg)](https://maizekit.github.io/)

[Website](https://maizekit.github.io/) · [Documentation](https://maizekit.github.io/docs/) · [Try a live maze](https://maizekit.github.io/m/moore-family-farm/)

</div>

## Overview

MaizeKit makes a small web app (a PWA) for each corn maze. Visitors open it on their
phone, allow location, and see a blue dot on the maze map with a line to the exit
from wherever they're standing.

It's static files on GitHub Pages: no server, no accounts, nothing to install for
visitors. Location is used on the phone and never sent anywhere.

## Getting started

Each maze is one folder, `m/<farm>/`, with a photo of the maze map and a
`maze.config.json` describing it.

1. Add a straight-on photo of the maze map as `m/<farm>/sign-photo.png`.
2. Describe it in `maze.config.json` next to it ([see Configuration](https://maizekit.github.io/docs/configuration/)).
3. Open a pull request. Publishing checks that the maze builds and that its exit can be reached.
4. Once merged, it's live at `https://maizekit.github.io/m/<farm>/`.

Each season, replace the photo and config. The farm's link and printed sign stay the
same, and git keeps every past year.

## Entrance sign

Every maze gets a printable sign with a QR code for its address at
`/m/<farm>/sign.html`.

## Repository

| Path | What it is |
|---|---|
| `index.html`, `style.css` | The website. |
| `app/` | The maze app, shared by every maze, and `build.py`, which turns a photo and config into the map. |
| `m/` | One folder per farm: its map photo and `maze.config.json`. |
| `docs/` | Documentation ([Starlight](https://starlight.astro.build/)). `docs/build.py` writes its pages from the code. |
| `brand/` | Icon, favicon, wordmark, badge and website images. |

`.github/workflows/pages.yml` builds every maze and the docs, and publishes the site on
every push to `main`.

## License

MaizeKit is [MIT licensed](LICENSE). The bundled [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js)
(BSD-3-Clause) and [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) (MIT) keep their own
licenses. Maze photos in `m/` belong to their farms.
