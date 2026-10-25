# maizekit.github.io

The MaizeKit website and brand assets, served at https://maizekit.github.io/.

| Path | What it is |
|---|---|
| `index.html`, `style.css`, `img/` | The website. |
| `docs/` | Documentation. `docs/index.html` is generated from the kit by `tools/build_docs.py`; don't edit it by hand. |
| `brand/` | Icon, favicon, wordmark and the "Built with MaizeKit" badge ([guide](brand/README.md)). |

Publishing is done by `.github/workflows/pages.yml` on every push and daily, so the docs
follow the kit automatically. To preview locally:

```sh
git clone https://github.com/MaizeKit/maizekit ../maizekit
python3 tools/build_docs.py ../maizekit
python3 -m http.server
```

The kit itself is [MaizeKit/maizekit](https://github.com/MaizeKit/maizekit).
