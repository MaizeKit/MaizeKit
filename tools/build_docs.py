"""Generates docs/index.html from a checkout of the MaizeKit kit repo.

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
OUT = Path("docs/index.html")
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


def render():
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

    toc = [("essentials", "Essentials"), ("configuration", "Configuration"), ("errors", "Errors"),
           ("settings", "Settings"), ("reference", "Reference"), ("build-tool", "Build tool")]

    parts = []
    parts.append(f"""
<div class="doc-head">
  <p class="eyebrow">Framework</p>
  <h1>MaizeKit</h1>
  <p class="abstract">{inline(abstract)}</p>
  <div class="availability">
    {f'<span>MaizeKit {esc(version)}+</span>' if version else ''}
    <span>Safari on iPhone</span><span>Chrome on Android</span><span>Any browser with location and WebGL</span>
  </div>
</div>
<section id="overview"><h2>Overview</h2>{markdown(readme_section(readme, "Overview"))}</section>
<nav class="topics-nav"><h2>Topics</h2><ul>{''.join(f'<li><a href="#{a}">{t}</a></li>' for a, t in toc)}</ul></nav>
""")

    parts.append(f'<section id="essentials"><h2>Essentials</h2><h3>Getting started</h3>{markdown(readme_section(readme, "Getting started"))}'
                 f'<h3>Entrance sign</h3>{markdown(readme_section(readme, "Entrance sign"))}</section>')

    rows = []
    for key, prop in schema["properties"].items():
        req = "Required" if key in schema.get("required", []) else "Optional"
        ex = prop.get("examples", [None])[0]
        ex_html = f'<pre><code>{esc(json.dumps({key: ex}))}</code></pre>' if ex is not None else ""
        rows.append(f'<div class="symbol" id="config-{key}"><h4><code>{key}</code> <span class="tag">{prop.get("type", "")}</span> <span class="tag">{req}</span></h4>'
                    f'<p>{inline(prop.get("description", ""))}</p>{ex_html}</div>')
    parts.append(f'<section id="configuration"><h2>Configuration</h2><p>{inline(schema.get("description", ""))}</p>'
                 f'<p>Defined in <a href="{REPO}/blob/main/maze.config.schema.json"><code>maze.config.schema.json</code></a>.</p>{"".join(rows)}</section>')

    err_rows = "".join(f"<tr><td><b>{esc(t)}</b></td><td>{esc(s)}</td></tr>" for t, s in errors)
    parts.append(f'<section id="errors"><h2>Errors</h2><p>Messages the app shows in red when something needs the visitor\'s attention.</p>'
                 f'<table><thead><tr><th>Message</th><th>What it tells the visitor</th></tr></thead><tbody>{err_rows}</tbody></table></section>')

    set_rows = "".join(f"<tr><td><code>{esc(s['name'])}</code></td><td><code>{esc(s['value'])}</code></td><td>{inline(s['summary'])}</td></tr>" for s in settings)
    parts.append(f'<section id="settings"><h2>Settings</h2><p>Constants in <code>app.js</code> you can change to tune behaviour.</p>'
                 f'<table><thead><tr><th>Name</th><th>Default</th><th>What it does</th></tr></thead><tbody>{set_rows}</tbody></table></section>')

    ref = []
    for sec in sections:
        syms = []
        for s in sec["symbols"]:
            params = ""
            if s["params"]:
                params = "<dl>" + "".join(f"<dt><code>{esc(n)}</code> <span class='tag'>{esc(t)}</span></dt><dd>{inline(d)}</dd>" for t, n, d in s["params"]) + "</dl>"
            ret = f"<p class='ret'><b>Returns</b> <code>{esc(s['returns'][0])}</code> {inline(s['returns'][1])}</p>" if s["returns"] else ""
            syms.append(f'<div class="symbol" id="{anchor(s["name"])}"><h4>{esc(s["name"])}</h4><p>{inline(s["summary"])}</p>'
                        f'<pre><code>{esc(s["decl"])}</code></pre>{params}{ret}</div>')
        ref.append(f'<h3 id="ref-{anchor(sec["title"])}">{esc(sec["title"])}</h3>{"".join(syms)}')
    parts.append(f'<section id="reference"><h2>Reference</h2><p>Everything in <a href="{REPO}/blob/main/app.js"><code>app.js</code></a>, grouped as it appears in the file.</p>{"".join(ref)}</section>')

    parts.append(f'<section id="build-tool"><h2>Build tool</h2><p><a href="{REPO}/blob/main/tools/build_assets.py"><code>tools/build_assets.py</code></a></p>'
                 f'<pre><code>{esc(build_doc)}</code></pre></section>')

    gen = f"Generated from <a href='{REPO}'>MaizeKit</a>" + (f" {esc(tag)}" if tag else "") + (f" (<a href='{REPO}/commit/{commit}'><code>{commit}</code></a>)" if commit else "")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MaizeKit documentation</title>
  <meta name="description" content="{esc(abstract)}">
  <link rel="icon" href="../brand/maizekit-favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../style.css">
  <link rel="stylesheet" href="docs.css">
</head>
<body>
  <header class="nav">
    <a class="nav-brand" href="../"><img src="../brand/maizekit-favicon.svg" alt="">MaizeKit</a>
    <nav><a href="./">Documentation</a><a href="{REPO}">GitHub</a></nav>
  </header>
  <main class="docs">
{''.join(parts)}
  </main>
  <footer><p class="fine">{gen}</p></footer>
</body>
</html>
"""


OUT.parent.mkdir(exist_ok=True)
OUT.write_text(render())
print(f"wrote {OUT}")
