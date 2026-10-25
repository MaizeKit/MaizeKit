# Settings

Values in `app.js` you can tune.

| Name | Default | What it does |
|---|---|---|
| `NEAR_FARM_M` | `1500` | Farther than this from the field (metres), the app says you're not at the maze. |
| `OUTSIDE_MARGIN_M` | `20` | How far past the field edge (metres) still counts as being in the maze. |
| `MAX_GPS_ACCURACY_M` | `50` | GPS fixes less accurate than this (metres) are ignored. |
| `ARRIVED_M` | `8` | Within this distance of the exit (metres), the app says you're at the exit. |
| `STORE_KEY` | `'maze-offset-v2'` | Browser storage key for the user's Fix my spot correction. |
| `LOCK_M` | `8` | Keep the current route while GPS stays within this distance of it (metres). |
| `OFF_ROUTE_FIXES` | `3` | Re-route after this many GPS fixes in a row are off the current route. |
