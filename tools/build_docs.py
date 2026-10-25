"""Generates the docs pages (docs/**/index.html) from a checkout of the MaizeKit kit repo.

Everything on the page comes from the kit itself, so the docs always match the code:
  README.md                 Overview and Getting started
  maze.config.schema.json   Configuration
  app.js                    Errors (alert messages), Settings and Reference (doc comments)
  tools/build_assets.py     Build tool
  git tags                  Availability

Usage: python tools/build_docs.py path/to/maizekit
Standard library only.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(sys.argv[1] if len(sys.argv) > 1 else "../maizekit")
REPO = "https://github.com/MaizeKit/maizekit"

esc = html.escape


# ---------- tiny Markdown (only what the kit README uses) ----------

def inline(text):
    text = esc(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)

    def link(m):
        href = m.group(2)
        if not re.match(r"https?:|#", href):
            href = f"{REPO}/blob/main/{href}"
        return f'<a href="{href}">{m.group(1)}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)


def markdown(md):
    out, lines, i = [], md.strip("\n").split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.lstrip().startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                code.append(lines[i].strip())
                i += 1
            out.append(f"<pre><code>{esc(chr(10).join(code))}</code></pre>")
            i += 1
        elif re.match(r"\d+\. ", line):
            items = []
            while i < len(lines) and (re.match(r"\d+\. ", lines[i]) or lines[i].startswith("   ")):
                if re.match(r"\d+\. ", lines[i]):
                    items.append([re.sub(r"^\d+\. ", "", lines[i])])
                else:
                    items[-1].append(lines[i][3:])
                i += 1
            out.append("<ol>" + "".join(f"<li>{markdown(chr(10).join(it))}</li>" for it in items) + "</ol>")
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(inline(lines[i][2:]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(\d+\. |- |```|#|\|)", lines[i].lstrip()):
                para.append(lines[i].strip())
                i += 1
            if para:
                out.append(f"<p>{inline(' '.join(para))}</p>")
            else:
                i += 1
    return "\n".join(out)


def readme_section(readme, title):
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", readme, re.S | re.M)
    return m.group(1) if m else ""


# ---------- app.js ----------

def parse_doc(raw):
    """A /** */ block -> (summary, params, returns)."""
    lines = [re.sub(r"^\s*\* ?", "", l) for l in raw.strip().split("\n")]
    text, params, returns = [], [], None
    for l in lines:
        m = re.match(r"@param \{([^}]*)\} (\[?[\w.]+(?:=[^\]]*)?\]?)\s*(.*)", l)
        if m:
            params.append(m.groups())
        elif l.startswith("@returns"):
            m = re.match(r"@returns \{([^}]*)\}\s*(.*)", l)
            returns = m.groups() if m else (l[9:], "")
        elif l.strip():
            text.append(l.strip())
    return " ".join(text), params, returns


def parse_app(src):
    sections, current = [], None
    settings = []
    # A section header, or a doc comment (one or more lines) followed by the line it documents.
    for m in re.finditer(r"^// ---------- (.+?) ----------$|^/\*\*(.*?)\*/\n([^\n]+)", src, re.S | re.M):
        if m.group(1):
            t = m.group(1).strip()
            current = {"title": t[0].upper() + t[1:], "symbols": []}
            sections.append(current)
            continue
        summary, params, returns = parse_doc(m.group(2))
        decl = m.group(3).rstrip(" {")
        if decl.startswith("const "):
            name = re.match(r"const (\w+)", decl).group(1)
            value = decl.split("=", 1)[1].strip().rstrip(";")
            settings.append({"name": name, "value": value, "summary": summary})
            continue
        name = re.match(r"(?:async )?(?:function|class) (\w+)", decl).group(1)
        if current is None:
            current = {"title": "General", "symbols": []}
            sections.append(current)
        current["symbols"].append({"name": name, "decl": decl, "summary": summary, "params": params, "returns": returns})
    return [s for s in sections if s["symbols"]], settings


def parse_errors(src):
    """Every alert the app can show: setHud('alert', title, subtitle)."""
    errors, seen = [], set()
    for m in re.finditer(r"setHud\('alert', (['`])(.+?)\1(?:, (['`])(.+?)\3)?", src):
        title = m.group(2)
        sub = m.group(4) or ""
        sub = re.sub(r"\$\{[^}]+\}", "…", sub)
        if title in seen:
            continue
        seen.add(title)
        errors.append((title, sub))
    return errors


# ---------- render ----------

def anchor(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


TOPICS = [
    # slug, title, one-line summary
    ("getting-started", "Getting started", "Make a site for your maze in six steps."),
    ("configuration", "Configuration", "Every field in maze.config.json."),
    ("errors", "Errors", "The messages visitors can see, and what they mean."),
    ("settings", "Settings", "Values in app.js you can tune."),
    ("reference", "Reference", "Every function in app.js, for contributors."),
    ("build-tool", "Build tool", "How tools/build_assets.py turns a photo into a map."),
]


def page(title, abstract, body, meta, crumb=True):
    """One docs page. Paths are site-absolute (the site is served from the domain root)."""
    head = '<p class="eyebrow">Framework</p>' if not crumb else '<p class="eyebrow"><a href="/docs/">MaizeKit</a></p>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}{' | MaizeKit' if crumb else ' documentation'}</title>
  <meta name="description" content="{esc(abstract)}">
  <link rel="icon" href="/brand/maizekit-favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/style.css">
  <link rel="stylesheet" href="/docs/docs.css">
</head>
<body>
  <header class="nav">
    <a class="nav-brand" href="/"><img src="/brand/maizekit-favicon.svg" alt="">MaizeKit</a>
    <nav><a href="/docs/">Documentation</a><a href="{REPO}">GitHub</a></nav>
  </header>
  <main class="docs">
    <div class="doc-head">{head}<h1>{esc(title)}</h1><p class="abstract">{inline(abstract)}</p>{meta}</div>
{body}
  </main>
  <footer><p class="fine">{FOOTER}</p></footer>
</body>
</html>
"""


def render():
    """Returns {output path: html} for every docs page."""
    global FOOTER
    readme = (KIT / "README.md").read_text()
    schema = json.loads((KIT / "maze.config.schema.json").read_text())
    app = (KIT / "app.js").read_text()
    build_doc = re.match(r'"""(.*?)"""', (KIT / "tools/build_assets.py").read_text(), re.S).group(1).strip()

    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(KIT), *args], capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            return ""

    tag = git("describe", "--tags", "--abbrev=0")
    version = tag.lstrip("v").removesuffix(".0") if tag else ""
    commit = git("rev-parse", "--short", "HEAD")
    abstract = re.search(r"^\*\*(.+?)\*\*$", readme, re.M).group(1)
    sections, settings = parse_app(app)
    errors = parse_errors(app)
    FOOTER = f"Generated from <a href='{REPO}'>MaizeKit</a>" + (f" {esc(tag)}" if tag else "") + \
        (f" (<a href='{REPO}/commit/{commit}'><code>{commit}</code></a>)" if commit else "")

    pages = {}

    # Landing: summary, availability, one overview paragraph, topics.
    availability = ('<div class="availability">' + (f'<span>MaizeKit {esc(version)}+</span>' if version else '') +
                    '<span>Safari on iPhone</span><span>Chrome on Android</span></div>')
    overview = readme_section(readme, "Overview").strip().split("\n\n")[0]
    topics = "".join(f'<li><a href="/docs/{slug}/"><b>{esc(t)}</b><span>{esc(d)}</span></a></li>' for slug, t, d in TOPICS)
    pages["docs/index.html"] = page("MaizeKit", abstract,
        f'<section><h2>Overview</h2>{markdown(overview)}</section><section><h2>Topics</h2><ul class="topic-list">{topics}</ul></section>',
        availability, crumb=False)

    pages["docs/getting-started/index.html"] = page("Getting started", TOPICS[0][2],
        markdown(readme_section(readme, "Getting started")) + "<h2>Entrance sign</h2>" + markdown(readme_section(readme, "Entrance sign")), "")

    rows = "".join(
        f'<tr><td><code>{k}</code></td><td>{"Required" if k in schema.get("required", []) else "Optional"}</td><td>{inline(p.get("description", ""))}</td></tr>'
        for k, p in schema["properties"].items())
    pages["docs/configuration/index.html"] = page("Configuration", TOPICS[1][2],
        f'<p>{inline(schema.get("description", ""))}</p><table><thead><tr><th>Field</th><th></th><th>What it is</th></tr></thead><tbody>{rows}</tbody></table>'
        f'<p>Start from <a href="{REPO}/blob/main/maze.config.example.json"><code>maze.config.example.json</code></a>. '
        f'The format is defined in <a href="{REPO}/blob/main/maze.config.schema.json"><code>maze.config.schema.json</code></a>.</p>', "")

    err_rows = "".join(f"<tr><td><b>{esc(t)}</b></td><td>{esc(s)}</td></tr>" for t, s in errors)
    pages["docs/errors/index.html"] = page("Errors", TOPICS[2][2],
        f'<table><thead><tr><th>Message</th><th>What it tells the visitor</th></tr></thead><tbody>{err_rows}</tbody></table>', "")

    set_rows = "".join(f"<tr><td><code>{esc(s['name'])}</code></td><td><code>{esc(s['value'])}</code></td><td>{inline(s['summary'])}</td></tr>" for s in settings)
    pages["docs/settings/index.html"] = page("Settings", TOPICS[3][2],
        f'<table><thead><tr><th>Name</th><th>Default</th><th>What it does</th></tr></thead><tbody>{set_rows}</tbody></table>', "")

    ref = []
    for sec in sections:
        items = []
        for s in sec["symbols"]:
            detail = ""
            if s["params"] or s["returns"]:
                params = "".join(f"<dt><code>{esc(n)}</code></dt><dd>{esc(t)} {inline(d)}</dd>" for t, n, d in s["params"])
                ret = f"<dt>Returns</dt><dd>{esc(s['returns'][0])} {inline(s['returns'][1])}</dd>" if s["returns"] else ""
                detail = f"<details><summary>Parameters</summary><pre><code>{esc(s['decl'])}</code></pre><dl>{params}{ret}</dl></details>"
            items.append(f'<li id="{anchor(s["name"])}"><code>{esc(s["name"])}</code> {inline(s["summary"])}{detail}</li>')
        ref.append(f'<h2>{esc(sec["title"])}</h2><ul class="symbols">{"".join(items)}</ul>')
    pages["docs/reference/index.html"] = page("Reference", TOPICS[4][2],
        f'<p>From the doc comments in <a href="{REPO}/blob/main/app.js"><code>app.js</code></a>, in file order.</p>{"".join(ref)}', "")

    pages["docs/build-tool/index.html"] = page("Build tool", TOPICS[5][2],
        f'<pre><code>{esc(build_doc)}</code></pre><p><a href="{REPO}/blob/main/tools/build_assets.py">View the source</a></p>', "")
    return pages


FOOTER = ""
for path, text in render().items():
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"wrote {out}")
