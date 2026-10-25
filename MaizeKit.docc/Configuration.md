# Configuration

Every field in `maze.config.json`.

Everything specific to one maze. Pixel coordinates are on the map after it's straightened to boardSize; the build saves that image as assets/sign-upright.jpg so you can read them off.

| Field |  | What it is |
|---|---|---|
| `name` | Required | The maze's name. Shown as the page title and on the entrance sign. |
| `photo` | Required | Path to a straight-on photo of the maze map. |
| `board` | Required | Four corners of the map board in the original photo: top-left, top-right, bottom-right, bottom-left. |
| `boardSize` | Required | Width and height to straighten the board to, in pixels. |
| `field` | Required | Outline of the corn field on the straightened map, as [x, y] points. Paths are the light areas inside it. |
| `openingEdge` | Required | Two points on the field edge where the entrance and exit are. A walkable strip just outside this edge connects the openings. |
| `hide` | Optional | Optional. Circles to ignore, such as a logo printed over the field. |
| `points` | Required | Entrance and exit on the straightened map. The app routes to the exit. |
| `ground` | Required | Four field corners on the map (sign) and where they are in the real world (lat, lon), for example read off satellite imagery. Used to place the map on the ground. |

Start from [`maze.config.example.json`](https://github.com/MaizeKit/maizekit/blob/main/maze.config.example.json). The format is defined in [`maze.config.schema.json`](https://github.com/MaizeKit/maizekit/blob/main/maze.config.schema.json).
