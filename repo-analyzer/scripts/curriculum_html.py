#!/usr/bin/env python3
"""
curriculum_html.py — Generate learn/curriculum.html from learn/curriculum.md.

The output is a single self-contained HTML file. Real interactive checkboxes
keyed by the curriculum's `<!-- step:SECTION:slug -->` markers, persisted to
localStorage. Native <details> dropdowns for checkpoints, hints, and
solutions. Markdown rendered client-side with marked.js (CDN), so updates to
curriculum.md require only a re-run of this script.

The "Export Markdown" button rebuilds curriculum.md with the current
check-state and copies it to the clipboard. Round-trip: edit checkboxes in
the browser, paste back to curriculum.md.

Usage:
    python curriculum_html.py [--curriculum learn/curriculum.md] [--output learn/curriculum.html] [--title "Learn Foo"]
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<style>
  :root {
    --bg: #fafafa; --fg: #1a1a1a; --muted: #6b7280; --accent: #2563eb;
    --row: #fff; --row-alt: #f3f4f6; --border: #e5e7eb; --done: #16a34a;
    --code-bg: #f3f4f6; --code-fg: #111;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1115; --fg: #e8e8e8; --muted: #9ca3af; --accent: #60a5fa;
      --row: #15181d; --row-alt: #1a1d22; --border: #2c2f33; --done: #22c55e;
      --code-bg: #1a1d22; --code-fg: #e8e8e8;
    }
  }
  * { box-sizing: border-box; }
  body {
    font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--fg); background: var(--bg);
    max-width: 920px; margin: 2rem auto; padding: 0 1.5rem 4rem;
  }
  h1, h2, h3, h4 { line-height: 1.25; }
  h1 { font-size: 1.9rem; margin: 0 0 .5rem; }
  h2 { font-size: 1.45rem; margin: 2.2rem 0 .8rem; padding-bottom: .3rem; border-bottom: 1px solid var(--border); }
  h3 { font-size: 1.15rem; margin: 1.8rem 0 .6rem; }
  h4 { font-size: 1rem; margin: 1.4rem 0 .5rem; color: var(--muted); }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  p, li { margin: .5em 0; }
  code {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: .9em; background: var(--code-bg); color: var(--code-fg);
    padding: 1px 5px; border-radius: 3px; border: 1px solid var(--border);
  }
  pre {
    background: var(--code-bg); color: var(--code-fg);
    padding: .85rem 1rem; border-radius: 6px; border: 1px solid var(--border);
    overflow-x: auto; line-height: 1.5;
  }
  pre code { background: none; padding: 0; border: 0; }
  blockquote {
    margin: 1em 0; padding: .4em 1em; color: var(--muted);
    border-left: 3px solid var(--border); background: var(--row-alt);
  }
  details {
    margin: .6em 0; padding: .4em .8em;
    border: 1px solid var(--border); border-radius: 4px;
    background: var(--row-alt);
  }
  details > summary { cursor: pointer; font-weight: 500; }
  details[open] { background: var(--row); }
  ul { padding-left: 1.6rem; }
  li.task-step { list-style: none; margin-left: -1.6rem; padding-left: 0; }
  li.task-step input[type=checkbox] {
    width: 18px; height: 18px; margin-right: .5em;
    vertical-align: -3px; cursor: pointer; accent-color: var(--done);
  }
  li.task-step.done > span.step-content { color: var(--muted); }
  li.task-step.done > span.step-content > a { color: var(--muted); }
  .toolbar {
    position: sticky; top: 0; z-index: 10; background: var(--bg);
    padding: .6rem 0; margin-bottom: 1rem;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: .8rem; flex-wrap: wrap;
  }
  .toolbar button {
    background: var(--row-alt); border: 1px solid var(--border); color: var(--fg);
    cursor: pointer; padding: 6px 14px; border-radius: 4px;
    font: .85rem -apple-system, sans-serif;
  }
  .toolbar button:hover { background: var(--accent); color: white; border-color: var(--accent); }
  .progress {
    flex: 1; min-width: 200px; height: 8px;
    background: var(--row-alt); border-radius: 4px;
    overflow: hidden; border: 1px solid var(--border);
  }
  .progress-fill {
    height: 100%; width: 0; background: var(--done);
    transition: width .3s ease;
  }
  .progress-label { color: var(--muted); font-size: .85rem; white-space: nowrap; }
  #export-modal {
    position: fixed; inset: 0; background: rgba(0,0,0,.5);
    display: none; align-items: center; justify-content: center; z-index: 100;
  }
  #export-modal.open { display: flex; }
  #export-modal .panel {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    padding: 1.5rem; max-width: 800px; width: 90%;
    max-height: 80vh; display: flex; flex-direction: column; gap: 1rem;
  }
  #export-modal textarea {
    flex: 1; min-height: 300px; font: 13px ui-monospace, monospace;
    background: var(--code-bg); color: var(--code-fg);
    border: 1px solid var(--border); border-radius: 4px; padding: .8rem;
    resize: vertical;
  }
  #export-modal .row { display: flex; gap: .6rem; justify-content: flex-end; }
</style>
</head>
<body>

<div class="toolbar">
  <div class="progress" title="Curriculum progress"><div class="progress-fill" id="progress-fill"></div></div>
  <span class="progress-label" id="progress-label">0 / 0</span>
  <button id="btn-export">Export Markdown</button>
  <button id="btn-reset">Reset progress</button>
</div>

<main id="content"><!-- rendered markdown lands here --></main>

<div id="export-modal" role="dialog" aria-modal="true">
  <div class="panel">
    <strong>Export curriculum.md with current check-state</strong>
    <p style="margin:0;color:var(--muted);font-size:.9rem;">
      Copied to clipboard. Paste back into <code>learn/curriculum.md</code> to
      sync your progress.
    </p>
    <textarea id="export-text" readonly></textarea>
    <div class="row">
      <button id="btn-copy">Copy again</button>
      <button id="btn-close">Close</button>
    </div>
  </div>
</div>

<script type="text/markdown" id="curriculum-src">__MARKDOWN__</script>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
const STORAGE_KEY = __STORAGE_KEY__;
const SRC = document.getElementById('curriculum-src').textContent;

// marked.js config: GFM with task lists, no auto-IDs (curriculum.md has explicit anchors)
marked.use({ gfm: true, breaks: false });

const html = marked.parse(SRC);
document.getElementById('content').innerHTML = html;

// Walk DOM, find HTML comments matching <!-- step:X.Y:slug -->, attach the next
// task-list <li> to that key. marked.js task lists render as <li> with a leading
// <input type="checkbox" disabled>.
const stepByKey = new Map();   // "1.3:read-foo" -> { li, input, key }
const orderedKeys = [];

function walkComments(root, fn) {
  const it = document.createNodeIterator(root, NodeFilter.SHOW_COMMENT);
  let n;
  while ((n = it.nextNode())) fn(n);
}

walkComments(document.getElementById('content'), (commentNode) => {
  const text = commentNode.nodeValue.trim();
  const m = text.match(/^step:([\\d.]+):([a-z0-9-]+)$/);
  if (!m) return;
  const key = `${m[1]}:${m[2]}`;

  // Find the immediately-following task-list <li>. The comment lives at the
  // same parent level as the next <ul>/<li>. Walk forward in document order.
  let nextEl = nextElementAfter(commentNode);
  let li = null;
  while (nextEl) {
    if (nextEl.tagName === 'UL' || nextEl.tagName === 'OL') {
      li = nextEl.querySelector('li');
      break;
    }
    if (nextEl.tagName === 'LI') { li = nextEl; break; }
    nextEl = nextEl.nextElementSibling;
  }
  if (!li) return;
  const input = li.querySelector('input[type=checkbox]');
  if (!input) return;

  li.classList.add('task-step');
  input.disabled = false;
  // Wrap the rest of li's content in a span for styling
  if (!li.querySelector('.step-content')) {
    const span = document.createElement('span');
    span.className = 'step-content';
    while (input.nextSibling) span.appendChild(input.nextSibling);
    li.appendChild(span);
  }
  stepByKey.set(key, { li, input, key });
  orderedKeys.push(key);
});

function nextElementAfter(node) {
  // Walk forward through siblings and up through ancestors looking for the
  // next Element node in document order.
  while (node) {
    let n = node.nextSibling;
    while (n) {
      if (n.nodeType === 1) return n;
      n = n.nextSibling;
    }
    node = node.parentNode;
    if (!node || node === document.body) return null;
  }
  return null;
}

// State
function loadState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}
function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

const state = loadState();

stepByKey.forEach(({ li, input, key }) => {
  input.checked = !!state[key];
  li.classList.toggle('done', input.checked);
  input.addEventListener('change', () => {
    state[key] = input.checked;
    saveState(state);
    li.classList.toggle('done', input.checked);
    updateProgress();
  });
});

function updateProgress() {
  const total = stepByKey.size;
  const done = Array.from(stepByKey.values()).filter(s => s.input.checked).length;
  document.getElementById('progress-fill').style.width = total ? (100 * done / total) + '%' : '0';
  document.getElementById('progress-label').textContent = `${done} / ${total}`;
}
updateProgress();

// Export: reconstruct curriculum.md with current check-state. The source is
// in SRC; for each <!-- step:X.Y:slug --> followed by a task-list bullet,
// patch the `[ ]` / `[x]` to match localStorage.
function exportMarkdown() {
  const lines = SRC.split('\\n');
  const markerRe = /<!--\\s*step:([\\d.]+):([a-z0-9-]+)\\s*-->/;
  const taskRe = /^(\\s*[-*]\\s*)\\[[ xX]\\](.*)$/;
  let pendingKey = null;
  const out = [];
  for (const line of lines) {
    const mm = line.match(markerRe);
    if (mm) {
      pendingKey = `${mm[1]}:${mm[2]}`;
      out.push(line);
      continue;
    }
    if (pendingKey) {
      const tm = line.match(taskRe);
      if (tm) {
        const checked = !!state[pendingKey];
        out.push(`${tm[1]}[${checked ? 'x' : ' '}]${tm[2]}`);
        pendingKey = null;
        continue;
      }
      // If we hit a non-blank, non-task line, give up matching this marker.
      if (line.trim() && !line.trim().startsWith('<!--')) {
        pendingKey = null;
      }
    }
    out.push(line);
  }
  return out.join('\\n');
}

function openExportModal() {
  const text = exportMarkdown();
  document.getElementById('export-text').value = text;
  document.getElementById('export-modal').classList.add('open');
  navigator.clipboard?.writeText(text).catch(() => {});
}

document.getElementById('btn-export').addEventListener('click', openExportModal);
document.getElementById('btn-close').addEventListener('click', () => {
  document.getElementById('export-modal').classList.remove('open');
});
document.getElementById('btn-copy').addEventListener('click', () => {
  const text = document.getElementById('export-text').value;
  navigator.clipboard?.writeText(text);
});
document.getElementById('btn-reset').addEventListener('click', () => {
  if (!confirm('Reset all checkbox progress?')) return;
  localStorage.removeItem(STORAGE_KEY);
  stepByKey.forEach(({ li, input, key }) => {
    input.checked = false;
    li.classList.remove('done');
    delete state[key];
  });
  updateProgress();
});
</script>

</body>
</html>
"""


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def derive_title(curriculum_text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", curriculum_text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def build_html(curriculum_path: Path, title: str | None) -> str:
    src = curriculum_path.read_text(encoding="utf-8")
    effective_title = title or derive_title(src, "Curriculum")
    storage_key = f"{slugify(effective_title)}-curriculum"

    # Escape only what would break the <script type="text/markdown"> container:
    # </script> sequences. Everything else passes through verbatim.
    safe_src = src.replace("</script", "<\\/script")

    return (
        TEMPLATE
        .replace("__TITLE__", html.escape(effective_title))
        .replace("__STORAGE_KEY__", json.dumps(storage_key))
        .replace("__MARKDOWN__", safe_src)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate curriculum.html from curriculum.md")
    parser.add_argument("--curriculum", default="learn/curriculum.md", help="Path to curriculum.md")
    parser.add_argument("--output", default="learn/curriculum.html", help="Output path")
    parser.add_argument("--title", help="Override page title (default: extract from curriculum's h1)")
    args = parser.parse_args()

    curriculum_path = Path(args.curriculum)
    if not curriculum_path.exists():
        print(f"error: {curriculum_path} not found")
        return 2

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_html(curriculum_path, args.title), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
