# maizekit.github.io

The MaizeKit website and brand assets, served at https://maizekit.github.io/.

| Path | What it is |
|---|---|
| `index.html`, `style.css`, `img/` | The website. |
| `MaizeKit.docc/` | DocC catalog. The articles are generated from the kit by `tools/build_docs.py`; only the icon and `theme-settings.json` live here. |
| `brand/` | Icon, favicon, wordmark and the "Built with MaizeKit" badge ([guide](brand/README.md)). |

Publishing is done by `.github/workflows/pages.yml` on every push and daily. It writes the
DocC catalog from the kit and builds it with Apple's DocC, so the docs follow the kit
automatically. To preview locally (needs Xcode or a Swift toolchain):

```sh
git clone https://github.com/MaizeKit/maizekit ../maizekit
python3 tools/build_docs.py ../maizekit
docc preview MaizeKit.docc
```

The kit itself is [MaizeKit/maizekit](https://github.com/MaizeKit/maizekit).
