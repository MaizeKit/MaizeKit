"""Generates a DocC documentation catalog (MaizeKit.docc) from a checkout of the MaizeKit kit repo.
Render it with Apple's DocC:  docc convert MaizeKit.docc --output-path _site/docs ...

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


# ---------- DocC catalog ----------
# Apple's documentation compiler (DocC) renders the catalog. Every article is generated
# from the kit, so nothing here is written by hand except the topic names.

OUT = Path("MaizeKit.docc")


def article(name, title, abstract, body):
    (OUT / f"{name}.md").write_text(f"# {title}\n\n{abstract}\n\n{body.strip()}\n")


def md_table(head, rows):
    esc_cell = lambda c: str(c).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(esc_cell(c) for c in r) + " |" for r in rows])


def build():
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
    abstract = re.search(r"^\*\*(.+?)\*\*$", readme, re.M).group(1)
    sections, settings = parse_app(app)
    errors = parse_errors(app)
    source = lambda path: f"{REPO}/blob/main/{path}"

    if OUT.exists():
        for f in OUT.glob("*.md"):
            f.unlink()
    (OUT / "Resources").mkdir(parents=True, exist_ok=True)

    available = f'  @Available("MaizeKit", introduced: "{version}")\n' if version else ""
    overview = readme_section(readme, "Overview").strip()
    (OUT / "MaizeKit.md").write_text(f"""# MaizeKit

@Metadata {{
  @TechnologyRoot
  @PageImage(purpose: icon, source: "maizekit-icon", alt: "MaizeKit icon")
{available}}}

{abstract}

## Overview

{overview}

## Topics

### Essentials

- <doc:GettingStarted>
- <doc:Configuration>

### Visitors

- <doc:Errors>
- <doc:Settings>

### Contributing

- <doc:Reference>
- <doc:BuildTool>
""")

    article("GettingStarted", "Getting Started", "Make a site for your maze in six steps.",
            readme_section(readme, "Getting started") + "\n## Entrance sign\n\n" + readme_section(readme, "Entrance sign"))

    rows = [(f"`{k}`", "Required" if k in schema.get("required", []) else "Optional", p.get("description", ""))
            for k, p in schema["properties"].items()]
    article("Configuration", "Configuration", "Every field in `maze.config.json`.",
            schema.get("description", "") + "\n\n" + md_table(["Field", "", "What it is"], rows) +
            f"\n\nStart from [`maze.config.example.json`]({source('maze.config.example.json')}). "
            f"The format is defined in [`maze.config.schema.json`]({source('maze.config.schema.json')}).")

    article("Errors", "Errors", "The messages visitors can see, and what they mean.",
            md_table(["Message", "What it tells the visitor"], [(f"**{t}**", s) for t, s in errors]))

    article("Settings", "Settings", "Values in `app.js` you can tune.",
            md_table(["Name", "Default", "What it does"], [(f"`{s['name']}`", f"`{s['value']}`", s["summary"]) for s in settings]))

    ref = [f"From the doc comments in [`app.js`]({source('app.js')}), in file order."]
    for sec in sections:
        ref.append(f"\n## {sec['title']}\n")
        for sym in sec["symbols"]:
            ref.append(f"### `{sym['name']}`\n\n{sym['summary']}\n\n```js\n{sym['decl']}\n```\n")
            if sym["params"]:
                ref.append("\n".join(f"- term `{n}`: {d} ({t})".replace("- term ", "- ") for t, n, d in sym["params"]) + "\n")
            if sym["returns"]:
                ref.append(f"Returns `{sym['returns'][0]}`. {sym['returns'][1]}\n")
    article("Reference", "Reference", "Every function in `app.js`, for contributors.", "\n".join(ref))

    article("BuildTool", "Build Tool", "How `tools/build_assets.py` turns a photo into a map.",
            f"```\n{build_doc}\n```\n\n[View the source]({source('tools/build_assets.py')})")

    print(f"wrote {OUT}/ ({len(list(OUT.glob('*.md')))} articles)")


build()
