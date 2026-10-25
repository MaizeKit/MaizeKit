# Contributing

Thanks for helping. MaizeKit is one repository: the app, the mazes, the docs and the website.

## Adding or updating a maze

If you run a maze, the easiest way is to [open an "Add my maze" request](https://github.com/MaizeKit/MaizeKit/issues/new?template=add-maze.yml).

To do it yourself, add `m/<farm>/sign-photo.png` and `m/<farm>/maze.config.json`
([configuration reference](https://maizekit.github.io/docs/configuration/)) and open a pull request.
The build checks that the config is complete and that the exit can be reached.

## Changing the app or docs

- The app is in `app/`. Every maze uses it, so a change here affects all of them.
- Document new functions and settings with a `/** */` comment in `app/app.js`; the docs'
  Reference and Settings pages are generated from those comments.
- The docs are written from the code by `docs/build.py`. Don't edit the generated pages in
  `docs/src/content/docs/docs/`; change the README, the schema or the code instead.

## Running it locally

```sh
# 1. Website and docs (needs Node). Starlight empties _site when it builds, so this goes first.
python3 docs/build.py && (cd docs && npm install && npm run build)

# 2. Every maze into _site/m/ (needs Python 3 with opencv-python-headless and numpy)
for farm in m/*/; do mkdir -p "_site/$farm" && cp -R app/. "_site/$farm" && cp "$farm"* "_site/$farm" && (cd "_site/$farm" && python3 build.py); done
cp -R brand _site/

python3 -m http.server -d _site
```

Location only works on `localhost` or HTTPS.

## Pull requests

Pull requests are squash-merged. `main` is protected and needs the build check to pass.
Merging publishes the site to https://maizekit.github.io/.
