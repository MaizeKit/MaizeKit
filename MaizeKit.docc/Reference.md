# Reference

Every function in `app.js`, for contributors.

From the doc comments in [`app.js`](https://github.com/MaizeKit/maizekit/blob/main/app.js), in file order.

## Coordinates

### `toEN`

Converts a longitude/latitude to metres east and north of the maze raster's origin.

```js
function toEN(lon, lat)
```

- `lon`:  (number)
- `lat`:  (number)

Returns `{e: number, n: number`. }

### `toLonLat`

Converts metres east/north of the raster origin back to longitude/latitude.

```js
function toLonLat(e, n)
```

- `e`: Metres east. (number)
- `n`: Metres north. (number)

Returns `[number, number]`. [lon, lat]

### `imgToGround`

Converts a maze raster pixel to ground metres, including the user's Fix my spot correction.

```js
function imgToGround(u, v)
```

- `u`: Pixel x. (number)
- `v`: Pixel y. (number)

Returns `{e: number, n: number`. }

### `groundToImg`

Converts ground metres to a maze raster pixel, including the user's Fix my spot correction.

```js
function groundToImg(e, n)
```

- `e`: Metres east. (number)
- `n`: Metres north. (number)

Returns `{u: number, v: number`. }

### `imgToLonLat`

Converts a maze raster pixel to longitude/latitude.

```js
function imgToLonLat(u, v)
```

- `u`: Pixel x. (number)
- `v`: Pixel y. (number)

Returns `[number, number]`. [lon, lat]

### `lonLatToImg`

Converts a longitude/latitude to a maze raster pixel.

```js
function lonLatToImg(lon, lat)
```

- `lon`:  (number)
- `lat`:  (number)

Returns `{u: number, v: number`. }

### `imageCorners`

The maze image's four corners on the map, for MapLibre's image source.

```js
function imageCorners()
```

Returns `Array<[number, number]>`. Top-left, top-right, bottom-right, bottom-left as [lon, lat].

### `saveOffset`

Saves the Fix my spot correction to browser storage.

```js
function saveOffset()
```

### `loadOffset`

Restores the Fix my spot correction from browser storage, if there is one.

```js
function loadOffset()
```


## Maze grid + routing

### `loadGrid`

Loads the walkable path grid from assets/walk.png into memory. Each cell holds 0 for corn, or a value that grows with distance from the nearest corn.

```js
async function loadGrid()
```

Returns `Promise<void>`. 

### `Heap`

A min-heap of grid cells keyed by distance, used by dijkstra() and buildRoute().

```js
class Heap
```

### `stepCost`

Cost of stepping into a cell. Cells near corn cost more, so routes keep to the middle of paths.

```js
function stepCost(g, base)
```

- `g`: Grid value of the cell (distance to corn). (number)
- `base`: Step length: 1 straight, √2 diagonal. (number)

Returns `number`. 

### `dijkstra`

Walking distance from one cell to every reachable cell on the path grid. Run once from the exit, so the way out from anywhere is a lookup.

```js
function dijkstra(startCell)
```

- `startCell`: Grid index to measure from. (number)

Returns `Float64Array`. Distance per cell; Infinity where unreachable.

### `snap`

Finds the nearest grid cell that has a path to the exit.

```js
function snap(u, v, maxR = 60)
```

- `u`: Pixel x. (number)
- `v`: Pixel y. (number)
- `[maxR=60]`: Search radius in cells. (number)

Returns `number`. Grid index, or -1 if none within the radius.

### `traceRoute`

Walks downhill on the distance-to-exit field from a cell to the exit.

```js
function traceRoute(fromCell)
```

- `fromCell`: Grid index to start from. (number)

Returns `Array<{u: number, v: number`. >} Route points in raster pixels.


## Geometry helpers

### `pointInPoly`

Whether a point is inside a polygon.

```js
function pointInPoly(u, v, poly)
```

- `u`:  (number)
- `v`:  (number)
- `poly`:  (Array<[number, number]>)

Returns `boolean`. 

### `distToPoly`

Distance from a point to a polygon's edge; 0 if inside.

```js
function distToPoly(u, v, poly)
```

- `u`:  (number)
- `v`:  (number)
- `poly`:  (Array<[number, number]>)

Returns `number`. Distance in raster pixels.


## Map

### `addLayers`

Adds the maze image, route line and position dot to the map.

```js
function addLayers()
```

### `drawMarks`

Places the EXIT and Entrance labels on the map.

```js
function drawMarks()
```

### `fitMaze`

Zooms the map to show the whole maze.

```js
function fitMaze(animate = true)
```

- `[animate=true]`:  (boolean)


## HUD

### `setHud`

Sets the status card at the top of the screen.

```js
function setHud(tone, title, sub = '')
```

- `tone`: '' for normal, 'alert' for a warning. (string)
- `title`:  (string)
- `[sub='']`: Smaller second line. (string)

### `currentImagePos`

Where the user is, in raster pixels: from GPS when it's accurate enough, otherwise the spot they last marked.

```js
function currentImagePos()
```

Returns `{u: number, v: number, kind: 'gps' | 'pin'`. | null}

### `metersPerScreenPx`

How many metres one screen pixel covers at the current zoom.

```js
function metersPerScreenPx(lat)
```

- `lat`:  (number)

Returns `number`. 


## Route locking

### `buildRoute`

Builds a route from a cell to the exit, with cumulative distances along it.

```js
function buildRoute(start)
```

- `start`: Grid index. (number)

Returns `{pts: Array<{u: number, v: number`. >, cum: number[], along: number, off: number, lastT: number}}

### `project`

Nearest point on a route to a position. Only searches between minAlong and maxAlong, since a maze route often doubles back one row away.

```js
function project(route, u, v, minAlong = -Infinity, maxAlong = Infinity)
```

- `route`: From buildRoute(). (object)
- `u`: Pixel x. (number)
- `v`: Pixel y. (number)
- `[minAlong=-Infinity]`: Metres along the route. (number)
- `[maxAlong=Infinity]`: Metres along the route. (number)

Returns `{u: number, v: number, i: number, d: number, along: number`. } d is metres off the route.

### `routeFor`

The route and the user's spot on it. Keeps the current route through small GPS jitter and re-routes only after OFF_ROUTE_FIXES fixes in a row are off it. @param {{u: number, v: number, kind: string}} pos From currentImagePos().

```js
function routeFor(pos)
```

Returns `{route: object, here: object`. | null}

### `refresh`

Redraws everything that depends on position: the dot, the route and the status card. Called on every GPS fix, tap and zoom.

```js
function refresh()
```


## Sensors

### `onGps`

Handles a new GPS fix from the browser.

```js
function onGps(p)
```

- `p`:  (GeolocationPosition)

### `onGpsError`

Handles a location error; shows how to turn location on if it was denied.

```js
function onGpsError(err)
```

- `err`:  (GeolocationPositionError)

### `startGps`

Starts watching the phone's location. The browser asks the user for permission.

```js
function startGps()
```

### `startCompass`

Starts reading the compass so Follow mode can turn the map. iPhone asks for permission.

```js
async function startCompass()
```

Returns `Promise<void>`. 


## Controls

### `setMode`

Switches between north-up and follow (map turns with the phone and stays centred on you).

```js
function setMode(mode)
```

- `mode`:  ('north' | 'track')


## Boot

### `snapRaw`

Nearest walkable cell, ignoring whether it reaches the exit. Used before the exit distances exist.

```js
function snapRaw(u, v)
```

- `u`:  (number)
- `v`:  (number)

Returns `number`. Grid index.

### `boot`

Starts the app: loads the maze data and path grid, works out distances from the exit, draws the map and starts GPS.

```js
async function boot()
```

Returns `Promise<void>`.
