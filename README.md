# maizekit.github.io

The MaizeKit website and brand assets, served at https://maizekit.github.io/.

| Path | What it is |
|---|---|
| `index.html`, `style.css`, `img/` | The website. |
| `docs/` | Documentation site ([Starlight](https://starlight.astro.build/)). Its pages are generated from the kit by `tools/build_docs.py`. |
| `brand/` | Icon, favicon, wordmark and the "Built with MaizeKit" badge ([guide](brand/README.md)). |

Publishing is done by `.github/workflows/pages.yml` on every push and daily. It writes the
docs pages from the kit and builds them with Starlight, so the docs follow the kit
automatically. To preview locally:

```sh
git clone https://github.com/MaizeKit/maizekit ../maizekit
python3 tools/build_docs.py ../maizekit
cd docs && npm install && npm run dev
```

The kit itself is [MaizeKit/maizekit](https://github.com/MaizeKit/maizekit).
