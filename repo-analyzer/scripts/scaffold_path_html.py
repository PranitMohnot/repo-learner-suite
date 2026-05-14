#!/usr/bin/env python3
"""
scaffold_path_html.py — Generate the learn/path.html clickable companion to
learn/README.md.

The output is a single self-contained .html file. No server, no build step.
Real clickable checkboxes persisting to localStorage. "Export progress"
button copies updated markdown to clipboard for round-trip paste into
README.md. Renders the same path table as README.md, but interactive.

Usage (from Claude Code):
    python scaffold_path_html.py --spec path_spec.json --output learn/path.html

Or import and call directly:
    from scaffold_path_html import generate_path_html, PathSpec, PathSection
    spec = PathSpec(...)
    generate_path_html(spec, "learn/path.html")

Convention: every curriculum section has an explicit anchor `<a id="s1.1">`
in curriculum.md (see repo-analyzer SKILL.md). The generated `read` URL for
each section is `curriculum.md#s{id}`. Override per-section if you need
something different.
"""

import argparse
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug. Mirrors scaffold_notebook.py."""
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


@dataclass
class PathSection:
    """One row in the path table.

    Fields:
        id: Section id like "1.1" (matches the curriculum anchor `s1.1`).
        phase: Phase number (1, 2, 3, ...). Used to group rows.
        title: Display title for the row.
        notebooks: List of (label, href) pairs. Empty list means "no exercise".
        quiz: The slash command the user should run to test themselves.
        read_url: Optional override for the curriculum link. Defaults to
            `curriculum.md#s{id}`.
    """

    id: str
    phase: int
    title: str
    notebooks: list[list[str]] = field(default_factory=list)
    quiz: str = ""
    read_url: Optional[str] = None

    def resolve(self) -> dict:
        """Project to the JSON shape consumed by the embedded JavaScript."""
        return {
            "id": self.id,
            "phase": self.phase,
            "title": self.title,
            "read": self.read_url or f"curriculum.md#s{self.id}",
            "notebooks": [list(n) for n in self.notebooks],
            "quiz": self.quiz or f"/learn quiz {self.id}",
        }


@dataclass
class PathSpec:
    """Full specification for one path.html.

    Fields:
        project_name: Used in the page title and h1.
        intro: One short HTML-safe paragraph below the h1. May contain inline
            tags like <code> or <a>.
        sections: List of PathSection rows.
        phase_names: dict mapping phase number to display name, e.g.
            {1: "Phase 1 — Usage", 2: "Phase 2 — Internals"}.
        storage_key: localStorage key. Defaults to "{slug}-learn-progress".
        footer_links: list of (label, href) pairs displayed in the footer's
            "what's where" map.
    """

    project_name: str
    intro: str
    sections: list[PathSection]
    phase_names: dict[int, str]
    storage_key: str = ""
    footer_links: list[list[str]] = field(default_factory=lambda: [
        ["README.md", "README.md"],
        ["overview.md", "overview.md"],
        ["curriculum.md", "curriculum.md"],
        ["cheatsheet.md", "cheatsheet.md"],
        ["notebooks/", "notebooks/"],
        ["internals/", "internals/"],
    ])

    def effective_storage_key(self) -> str:
        return self.storage_key or f"{slugify(self.project_name)}-learn-progress"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Learn {{TITLE}} — Path</title>
<style>
  :root {
    --bg: #fafafa; --fg: #1a1a1a; --muted: #777; --accent: #2563eb;
    --row: #fff; --row-alt: #f3f3f3; --border: #e2e2e2; --done: #16a34a;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #15171a; --fg: #e8e8e8; --muted: #999; --accent: #60a5fa;
      --row: #1c1f23; --row-alt: #1f2226; --border: #2c2f33; --done: #22c55e;
    }
  }
  * { box-sizing: border-box; }
  body {
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--fg); background: var(--bg);
    max-width: 980px; margin: 2rem auto; padding: 0 1.5rem;
  }
  h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
  h2 {
    font-size: 1.1rem; margin: 2rem 0 .5rem; padding-bottom: .25rem;
    border-bottom: 1px solid var(--border);
  }
  p.intro { color: var(--muted); margin: 0 0 1.5rem; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  code {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: .85em; background: var(--row-alt);
    padding: 1px 5px; border-radius: 3px; border: 1px solid var(--border);
  }
  .progress-wrap { margin: .5rem 0 1rem; }
  .progress-label {
    display: flex; justify-content: space-between;
    color: var(--muted); font-size: .85rem; margin-bottom: 4px;
  }
  .progress-bar {
    height: 8px; background: var(--row-alt); border-radius: 4px;
    overflow: hidden; border: 1px solid var(--border);
  }
  .progress-fill {
    height: 100%; width: 0; background: var(--done);
    transition: width .3s ease;
  }
  table { width: 100%; border-collapse: collapse; margin-bottom: .5rem; }
  th, td {
    text-align: left; padding: .55rem .65rem;
    border-bottom: 1px solid var(--border); vertical-align: top;
  }
  tr:nth-child(even) td { background: var(--row-alt); }
  tr:nth-child(odd) td { background: var(--row); }
  th {
    background: var(--bg); font-size: .8rem;
    text-transform: uppercase; letter-spacing: .03em;
    color: var(--muted); font-weight: 600;
  }
  td.check { width: 38px; text-align: center; }
  td.num { width: 44px; color: var(--muted); font-variant-numeric: tabular-nums; }
  td.title { font-weight: 500; }
  tr.done td.title { color: var(--muted); text-decoration: line-through; }
  input[type=checkbox] {
    width: 18px; height: 18px; cursor: pointer; accent-color: var(--done);
  }
  .copy-btn {
    background: none; border: 1px solid var(--border); color: var(--muted);
    cursor: pointer; padding: 2px 8px; border-radius: 3px;
    font: .8rem ui-monospace, "SF Mono", monospace;
  }
  .copy-btn:hover { background: var(--row-alt); color: var(--fg); }
  .actions {
    display: flex; gap: .5rem; flex-wrap: wrap; margin: 2rem 0 1rem;
  }
  .actions button {
    background: var(--accent); color: white; border: none;
    padding: .5rem .9rem; border-radius: 4px; cursor: pointer; font-size: .9rem;
  }
  .actions button.secondary {
    background: transparent; color: var(--accent); border: 1px solid var(--accent);
  }
  dialog {
    border: 1px solid var(--border); border-radius: 6px;
    background: var(--bg); color: var(--fg); max-width: 700px; padding: 1rem;
  }
  dialog::backdrop { background: rgba(0,0,0,.5); }
  textarea {
    width: 100%; height: 240px; font: .85rem ui-monospace, monospace;
    background: var(--row-alt); color: var(--fg);
    border: 1px solid var(--border); border-radius: 4px; padding: .5rem;
  }
  footer { margin-top: 3rem; color: var(--muted); font-size: .85rem; }
  .links { display: flex; gap: .5rem; flex-wrap: wrap; }
  .links a { white-space: nowrap; }
</style>
</head>
<body>

<h1>Learn {{TITLE}}</h1>
<p class="intro">{{INTRO_HTML}}</p>

<div class="progress-wrap">
  <div class="progress-label">
    <span><strong id="doneCount">0</strong> of <span id="totalCount">0</span> sections complete</span>
    <span id="pctLabel">0%</span>
  </div>
  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
</div>

<div id="phases"></div>

<div class="actions">
  <button id="exportBtn">Export progress as markdown</button>
  <button class="secondary" id="resetBtn">Reset all checkboxes</button>
</div>

<footer>
  <p><strong>What's where:</strong></p>
  <div class="links" id="footerLinks"></div>
  <p style="margin-top:1rem">
    State stored under localStorage key <code>{{STORAGE_KEY}}</code>.
    Open notebooks in Jupyter or your IDE.
  </p>
</footer>

<dialog id="exportDialog">
  <p><strong>Markdown for your README.md:</strong></p>
  <textarea id="exportText" readonly></textarea>
  <div style="margin-top:.5rem; display:flex; gap:.5rem; justify-content:flex-end">
    <button id="copyExport">Copy to clipboard</button>
    <button class="secondary" id="closeExport">Close</button>
  </div>
</dialog>

<script>
const STORAGE_KEY = '{{STORAGE_KEY}}';
const sections = {{SECTIONS_JSON}};
const phaseNames = {{PHASE_NAMES_JSON}};
const footerLinks = {{FOOTER_LINKS_JSON}};

function loadState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}
function saveState(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }

function render() {
  const state = loadState();
  const phasesEl = document.getElementById('phases');
  phasesEl.innerHTML = '';
  const phases = [...new Set(sections.map(s => s.phase))].sort((a, b) => a - b);
  for (const p of phases) {
    const h = document.createElement('h2');
    h.textContent = phaseNames[p] || ('Phase ' + p);
    phasesEl.appendChild(h);

    const table = document.createElement('table');
    table.innerHTML = `
      <thead><tr>
        <th></th><th>#</th><th>Section</th><th>Read</th>
        <th>Do</th><th>Test</th>
      </tr></thead><tbody></tbody>`;
    const tbody = table.querySelector('tbody');
    for (const s of sections.filter(s => s.phase === p)) {
      const done = !!state[s.id];
      const tr = document.createElement('tr');
      if (done) tr.classList.add('done');
      const notebookLinks = (s.notebooks || [])
        .map(([label, href]) => `<a href="${href}">${label}</a>`)
        .join(' · ') || '—';
      tr.innerHTML = `
        <td class="check">
          <input type="checkbox" data-id="${s.id}" ${done ? 'checked' : ''}>
        </td>
        <td class="num">${s.id}</td>
        <td class="title">${s.title}</td>
        <td><a href="${s.read}">§${s.id}</a></td>
        <td>${notebookLinks}</td>
        <td>
          <code>${s.quiz}</code>
          <button class="copy-btn" data-copy="${s.quiz}">copy</button>
        </td>`;
      tbody.appendChild(tr);
    }
    phasesEl.appendChild(table);
  }
  attachHandlers();
  updateProgress();
}

function renderFooterLinks() {
  const el = document.getElementById('footerLinks');
  el.innerHTML = footerLinks
    .map(([label, href], i) => {
      const sep = i === footerLinks.length - 1 ? '' : ' · ';
      return `<span><a href="${href}">${label}</a>${sep}</span>`;
    })
    .join('');
}

function attachHandlers() {
  for (const cb of document.querySelectorAll('input[type=checkbox][data-id]')) {
    cb.onchange = (e) => {
      const state = loadState();
      state[e.target.dataset.id] = e.target.checked;
      saveState(state);
      render();
    };
  }
  for (const btn of document.querySelectorAll('.copy-btn[data-copy]')) {
    btn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        const orig = btn.textContent;
        btn.textContent = 'copied';
        setTimeout(() => btn.textContent = orig, 1200);
      } catch { /* ignore */ }
    };
  }
}

function updateProgress() {
  const state = loadState();
  const total = sections.length;
  const done = sections.filter(s => state[s.id]).length;
  const pct = total ? Math.round((done / total) * 100) : 0;
  document.getElementById('doneCount').textContent = done;
  document.getElementById('totalCount').textContent = total;
  document.getElementById('pctLabel').textContent = pct + '%';
  document.getElementById('progressFill').style.width = pct + '%';
}

function exportMarkdown() {
  const state = loadState();
  const phases = [...new Set(sections.map(s => s.phase))].sort((a, b) => a - b);
  const lines = ['# Learn {{TITLE}} — progress export', ''];
  for (const p of phases) {
    lines.push('## ' + (phaseNames[p] || ('Phase ' + p)));
    for (const s of sections.filter(s => s.phase === p)) {
      const mark = state[s.id] ? '[x]' : '[ ]';
      lines.push(`- ${mark} ${s.id} — ${s.title}`);
    }
    lines.push('');
  }
  return lines.join('\\n');
}

document.getElementById('exportBtn').onclick = openExport;
function openExport() {
  document.getElementById('exportText').value = exportMarkdown();
  document.getElementById('exportDialog').showModal();
}
document.getElementById('copyExport').onclick = async () => {
  try {
    await navigator.clipboard.writeText(document.getElementById('exportText').value);
    document.getElementById('copyExport').textContent = 'Copied';
    setTimeout(() => document.getElementById('copyExport').textContent = 'Copy to clipboard', 1200);
  } catch {}
};
document.getElementById('closeExport').onclick = () =>
  document.getElementById('exportDialog').close();
document.getElementById('resetBtn').onclick = () => {
  if (confirm('Reset all progress?')) { localStorage.removeItem(STORAGE_KEY); render(); }
};

renderFooterLinks();
render();
</script>

</body>
</html>
"""


def generate_path_html(spec: PathSpec, output_path: str) -> str:
    """Render a PathSpec into a self-contained .html file."""
    sections_payload = [s.resolve() for s in spec.sections]
    # Phase keys must be strings in JSON; render as such
    phase_names_payload = {str(k): v for k, v in spec.phase_names.items()}

    html = HTML_TEMPLATE
    html = html.replace("{{TITLE}}", _html_escape(spec.project_name))
    html = html.replace("{{INTRO_HTML}}", spec.intro)
    html = html.replace("{{STORAGE_KEY}}", _js_escape(spec.effective_storage_key()))
    html = html.replace("{{SECTIONS_JSON}}", json.dumps(sections_payload, indent=2))
    html = html.replace("{{PHASE_NAMES_JSON}}", json.dumps(phase_names_payload))
    html = html.replace("{{FOOTER_LINKS_JSON}}", json.dumps([list(p) for p in spec.footer_links]))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _js_escape(s: str) -> str:
    # Single quotes need escaping; the localStorage key lives inside single quotes
    return s.replace("\\", "\\\\").replace("'", "\\'")


def from_json(spec_path: str) -> PathSpec:
    """Load a PathSpec from a JSON file.

    Expected schema:
    {
      "project_name": "...",
      "intro": "...",
      "phase_names": {"1": "Phase 1 — ...", "2": "..."},
      "storage_key": "...",            // optional
      "footer_links": [["label", "href"], ...],  // optional
      "sections": [
        {"id": "1.1", "phase": 1, "title": "...", "notebooks": [["Ex 1", "..."]],
         "quiz": "/learn quiz 1.1", "read_url": null},
        ...
      ]
    }
    """
    with open(spec_path) as f:
        data = json.load(f)
    sections = [
        PathSection(
            id=item["id"],
            phase=int(item["phase"]),
            title=item["title"],
            notebooks=[list(n) for n in item.get("notebooks", [])],
            quiz=item.get("quiz", ""),
            read_url=item.get("read_url"),
        )
        for item in data["sections"]
    ]
    return PathSpec(
        project_name=data["project_name"],
        intro=data["intro"],
        sections=sections,
        phase_names={int(k): v for k, v in data["phase_names"].items()},
        storage_key=data.get("storage_key", ""),
        footer_links=[list(p) for p in data.get(
            "footer_links",
            [
                ["README.md", "README.md"],
                ["overview.md", "overview.md"],
                ["curriculum.md", "curriculum.md"],
                ["cheatsheet.md", "cheatsheet.md"],
                ["notebooks/", "notebooks/"],
                ["internals/", "internals/"],
            ],
        )],
    )


def main():
    parser = argparse.ArgumentParser(description="Generate learn/path.html from a spec")
    parser.add_argument("--spec", required=True, help="Path to path-spec JSON")
    parser.add_argument(
        "--output", default="learn/path.html", help="Output .html path (default: learn/path.html)"
    )
    args = parser.parse_args()

    spec = from_json(args.spec)
    out = generate_path_html(spec, args.output)
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
