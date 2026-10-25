"""Checks that every internal link and asset in the built site exists.

Usage: python3 .github/scripts/check_links.py _site
Exits non-zero, listing each broken link, if any are missing. Standard library only.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

root = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
broken = []
checked = 0
for page in root.rglob("*.html"):
    html = page.read_text(errors="ignore")
    for ref in re.findall(r'(?:href|src)="([^"#?]+)', html):
        if re.match(r"[a-z]+:", ref) or ref.startswith("//"):
            continue  # external, mailto, data, etc.
        path = unquote(urlparse(ref).path)
        target = (root / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
        target = target.resolve()
        checked += 1
        if not (target.is_file() or (target / "index.html").is_file()):
            broken.append(f"{page.relative_to(root)} -> {ref}")

print(f"checked {checked} internal links in {len(list(root.rglob('*.html')))} pages")
if broken:
    print("broken:\n  " + "\n  ".join(sorted(set(broken))))
    sys.exit(1)
