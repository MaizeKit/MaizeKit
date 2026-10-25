"""Builds the georeferenced maze overlay and routing grid from a photo of the maze map.

The sign is warped (homography) onto the real field outline, so every output is a
north-up raster: pixel (x, y) -> east = x * RES, north = -y * RES from ORIGIN.

Usage: python build.py [maze.config.json]   (run from the folder that holds the config)
Needs: opencv-python-headless, numpy
"""
import json, math, sys
from pathlib import Path
import cv2
import numpy as np

# Everything specific to one maze lives in the config file (see README).
CONFIG = sys.argv[1] if len(sys.argv) > 1 else "maze.config.json"
cfg = json.load(open(CONFIG))
# Check the config has every field the format requires (see maze.config.schema.json).
schema = json.load(open(Path(__file__).with_name("maze.config.schema.json")))
missing = [k for k in schema["required"] if k not in cfg]
missing += [f"points.{k}" for k in schema["properties"]["points"]["required"] if k not in cfg.get("points", {})]
if missing:
    sys.exit(f"{CONFIG} is missing: {', '.join(missing)}")
OUT = "assets"
Path(OUT).mkdir(exist_ok=True)

# Corners of the sign board in the photo, in upright order: TL, TR, BR, BL.
BOARD = np.float32(cfg["board"])
W, H = cfg["boardSize"]
# Outline of the corn field on the upright sign.
FIELD = np.array(cfg["field"], np.int32)
# The field edge the entrance/exit open onto; a walkable strip outside it joins them.
BOTTOM_L, BOTTOM_R = (tuple(p) for p in cfg["openingEdge"])
POINTS = {k: tuple(v) for k, v in cfg["points"].items()}
# Sign field corners -> where they sit on the ground (lat, lon).
GROUND = [(tuple(g["sign"]), (g["lat"], g["lon"])) for g in cfg["ground"]]

RES = 0.15  # metres per output pixel
CELL = 2  # output pixels per routing cell (0.3 m)
MIN_CONNECTED = 0.9  # below this share of path connected to the exit, visitors see a notice
MIN_PATH_M = 1.2  # narrower than this isn't a walkable path (e.g. a planter gap between corn rows)
MARGIN_M = 12

# ---------- straighten the sign ----------

photo = cv2.imread(cfg["photo"])
M = cv2.getPerspectiveTransform(BOARD, np.float32([(0, 0), (W, 0), (W, H), (0, H)]))
sign = cv2.warpPerspective(photo, M, (W, H), flags=cv2.INTER_CUBIC)

field = np.zeros((H, W), np.uint8)
cv2.fillPoly(field, [FIELD], 1)
for h in cfg.get("hide", []):  # e.g. a logo printed over the field
    cv2.circle(field, tuple(h["circle"][:2]), h["circle"][2], 0, -1)

def otsu3_low_cutoff(values):
    """Splits colour distances into three groups (corn, light paths, dark paths) the way
    Otsu's method does for two, and returns the upper edge of the group nearest the corn."""
    hist = np.bincount(values, minlength=256).astype(np.float64)
    p = hist / hist.sum()
    w = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    total = mu[-1]
    best, cut = -1.0, 0
    for t1 in range(1, 254):
        w0, m0 = w[t1], mu[t1]
        if w0 <= 0:
            continue
        for t2 in range(t1 + 1, 255):
            w1, m1 = w[t2] - w0, mu[t2] - m0
            w2, m2 = 1 - w[t2], total - mu[t2]
            if w1 <= 0 or w2 <= 0:
                continue
            between = m0 * m0 / w0 + m1 * m1 / w1 + m2 * m2 / w2
            if between > best:
                best, cut = between, t1
    return cut


# Find the paths by learning what corn looks like in this photo: most of a maze is corn,
# so the typical colour inside the field is the corn colour. Anything clearly different
# from it (darker, lighter, browner) is path. Works for painted signs and aerial photos.
blur = cv2.medianBlur(sign, 7)
colour = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB).astype(np.float32)
inside = field > 0
corn_colour = np.median(colour[inside], axis=0)
diff = np.linalg.norm(colour - corn_colour, axis=2)
d8 = np.clip(diff * 2, 0, 255).astype(np.uint8)
if cfg.get("detector") == "learned":
    green = d8 <= otsu3_low_cutoff(d8[inside])
else:
    # Classic rule for painted signs: corn is dark, saturated green.
    green = (cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)[..., 2] < 100) & (cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)[..., 1] > 60)

walk = ((field > 0) & ~green).astype(np.uint8)
# Drop anything too narrow to walk. The map's scale comes from the field's real size.
def _metres(a, b):
    (la1, lo1), (la2, lo2) = a, b
    return math.hypot((la1 - la2) * 110540, (lo1 - lo2) * 111320 * math.cos(math.radians(la1)))
sign_px = np.mean([math.dist(GROUND[i][0], GROUND[i - 1][0]) for i in range(4)])
ground_m = np.mean([_metres(GROUND[i][1], GROUND[i - 1][1]) for i in range(4)])
k = max(3, int(round(MIN_PATH_M / (ground_m / sign_px))) | 1) if cfg.get("detector") == "learned" else 3
walk = cv2.morphologyEx(walk, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)) if k > 3 else np.ones((3, 3), np.uint8))
n, lbl, st, _ = cv2.connectedComponentsWithStats(walk, 8)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < 1000:  # specks, e.g. texture inside lettering
        walk[lbl == i] = 0

# A walkable strip just outside the bottom edge, so openings connect to each other.
band = np.zeros_like(walk)
cv2.fillPoly(band, [np.array([BOTTOM_L, BOTTOM_R, (BOTTOM_R[0], BOTTOM_R[1] + 30), (BOTTOM_L[0], BOTTOM_L[1] + 30)], np.int32)], 1)
band[field > 0] = 0
walk |= band

alpha = np.zeros((H, W), np.uint8)
cv2.fillPoly(alpha, [FIELD], 255)
alpha[band > 0] = 255
for h in cfg.get("hide", []):
    cv2.circle(alpha, tuple(h["circle"][:2]), h["circle"][2], 0, -1)

# ---------- sign -> ground ----------

lat0 = sum(g[1][0] for g in GROUND) / 4
lon0 = sum(g[1][1] for g in GROUND) / 4
M_LAT = 110540.0
M_LON = 111320.0 * math.cos(math.radians(lat0))
en = np.array([((lon - lon0) * M_LON, (lat - lat0) * M_LAT) for _, (lat, lon) in GROUND], np.float64)
e_min, n_max = en[:, 0].min() - MARGIN_M, en[:, 1].max() + MARGIN_M
e_max, n_min = en[:, 0].max() + MARGIN_M, en[:, 1].min() - MARGIN_M
OW = int(math.ceil((e_max - e_min) / RES / CELL)) * CELL
OH = int(math.ceil((n_max - n_min) / RES / CELL)) * CELL
dst = np.float32([((e - e_min) / RES, (n_max - n) / RES) for e, n in en])
Hg = cv2.getPerspectiveTransform(np.float32([s for s, _ in GROUND]), dst)

def to_out(pts):
    return cv2.perspectiveTransform(np.float32(pts).reshape(-1, 1, 2), Hg).reshape(-1, 2)

out_img = cv2.warpPerspective(sign, Hg, (OW, OH), flags=cv2.INTER_CUBIC)
out_alpha = cv2.warpPerspective(alpha, Hg, (OW, OH), flags=cv2.INTER_LINEAR)
out_walk = cv2.warpPerspective(walk * 255, Hg, (OW, OH), flags=cv2.INTER_LINEAR)
cv2.imwrite(f"{OUT}/maze.webp", np.dstack([out_img, out_alpha]), [cv2.IMWRITE_WEBP_QUALITY, 85])
cv2.imwrite(f"{OUT}/sign-upright.jpg", sign, [cv2.IMWRITE_JPEG_QUALITY, 85])

# Routing grid: value = distance to nearest corn (in cells, x DIST_SCALE), 0 = blocked.
DIST_SCALE = 20
small = cv2.resize(out_walk, (OW // CELL, OH // CELL), interpolation=cv2.INTER_AREA) > 127
small = small.astype(np.uint8)
dist = cv2.distanceTransform(small, cv2.DIST_L2, 5)
grid = np.clip(np.round(dist * DIST_SCALE), 0, 255).astype(np.uint8)
grid[(small > 0) & (grid == 0)] = 1
cv2.imwrite(f"{OUT}/walk.png", grid)

# Sanity check: entrance and exit must connect.
nc, lab = cv2.connectedComponents(small, connectivity=8)
def cell_label(p):
    x, y = (to_out([p])[0] / CELL).astype(int)
    win = lab[y - 4:y + 5, x - 4:x + 5]
    vals = win[win > 0]
    return np.bincount(vals).argmax() if len(vals) else 0
# Path checks warn rather than fail: the maze still publishes, and visitors see a notice.
warnings = []
if not (cell_label(POINTS["entrance"]) == cell_label(POINTS["exit"]) != 0):
    warnings.append("The entrance and exit may not be connected on this map.")

# How much of the maze is one connected network. A low score means the paths weren't read
# cleanly (shadows, glare, a logo) and some routes would be missing, so stop the build.
exit_label = cell_label(POINTS["exit"])
connected = float((lab == exit_label).sum()) / max(1, int((lab > 0).sum()))
print(f"paths: {connected:.0%} of the maze connects to the exit")
if connected < MIN_CONNECTED:
    warnings.append(f"Only {connected:.0%} of this maze's paths could be traced to the exit, so some routes may be missing.")
for w in warnings:
    print("warning:", w)

_top, _bottom = to_out([(W / 2, H * 0.4), (W / 2, H * 0.6)])
sign_bearing = round(math.degrees(math.atan2(_top[0] - _bottom[0], _bottom[1] - _top[1])) % 360, 1)
field_out = to_out(FIELD).round(1).tolist()
points_out = {k: dict(zip(("x", "y"), to_out([p])[0].round(1).tolist())) for k, p in POINTS.items()}
meta = {
    "name": cfg["name"],
    "notice": " ".join([cfg.get("notice", "")] + warnings).strip(),
    # Compass direction the top of the map photo faces, so the app can open turned to match it.
    "signBearing": sign_bearing,
    "signAspect": W / H,
    "width": OW, "height": OH, "res": RES, "cell": CELL,
    "gridWidth": OW // CELL, "gridHeight": OH // CELL, "distScale": DIST_SCALE,
    # top-left corner of the raster and metres-per-degree used to build it
    "origin": {"lat": float(lat0 + n_max / M_LAT), "lon": float(lon0 + e_min / M_LON)},
    "mPerDeg": {"lat": M_LAT, "lon": M_LON},
    "field": field_out,
    "points": points_out,
}
with open(f"{OUT}/maze.json", "w") as f:
    json.dump(meta, f, indent=1)

print("raster", OW, OH, "grid", OW // CELL, OH // CELL, "field", round((e_max - e_min) - 2 * MARGIN_M), "x", round((n_max - n_min) - 2 * MARGIN_M), "m")
