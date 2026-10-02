"""Materialize a Create development into a static prototype inside a sandbox.

``howlcreate develop`` designs; this module builds. It takes a
``howl.development_result/v1`` whose ``sandbox_prototype_design`` carries
HowlWriter copy (``writer_copy``) and, optionally, a page structure
(``page``) that Create's model-backed development proposed, and renders a
small static site: HTML, CSS, the copy as JSON, the design notes as
Markdown, and ``create-artifact-manifest.json`` recording the provenance
of every file.

Rendering is deterministic and performs no inference: the same
development always yields byte-identical artifacts (only the manifest
timestamp differs). Copy text is never invented here. Each slot renders
Writer's proposal when it was ``FACTUALLY_PRESERVED`` and the current copy
otherwise, and the manifest names every withheld proposal.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from howlcreate.engine.candidate_ingestion import IngestionError, validate_envelope
from howlcreate.engine.sandbox import SandboxRoot

MANIFEST_NAME = "create-artifact-manifest.json"
MANIFEST_SCHEMA = "howlcreate.artifact_manifest/v1"
LAYOUTS = frozenset({"hero", "cards", "list", "text"})
_SLUG = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_MEDIA = {
    ".html": "text/html",
    ".css": "text/css",
    ".json": "application/json",
    ".md": "text/markdown",
    ".js": "text/javascript",
}

STYLESHEET = """:root {
  color-scheme: light dark;
  --bg: #ffffff; --fg: #1b1f24; --muted: #57606a; --line: #d0d7de;
  --card: #f6f8fa; --accent: #0b5cad; --focus: #b35900;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0d1117; --fg: #e6edf3; --muted: #9da7b3; --line: #30363d;
          --card: #161b22; --accent: #6cb6ff; --focus: #f0a35e; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
       font: 1rem/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
a { color: var(--accent); }
:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
.wrap { max-width: 68rem; margin: 0 auto; padding: 0 16px; }
header.hero { padding: 3rem 0 2rem; border-bottom: 1px solid var(--line); }
header.hero h1 { font-size: clamp(1.75rem, 5vw, 2.75rem); line-height: 1.15; margin: 0 0 .75rem; }
header.hero p { color: var(--muted); font-size: 1.1rem; margin: .25rem 0; }
section { padding: 2rem 0; border-bottom: 1px solid var(--line); }
section h2 { font-size: 1.35rem; margin: 0 0 1rem; }
.cards { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
         list-style: none; margin: 0; padding: 0; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 1rem; }
.card h3 { font-size: 1.05rem; margin: 0 0 .35rem; }
.card .meta { color: var(--muted); font-size: .9rem; margin: 0 0 .5rem; }
.card p { margin: 0; }
ul.list { padding-left: 1.25rem; }
footer { padding: 2rem 0; color: var(--muted); font-size: .85rem; }
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _copy_index(slot: dict) -> dict[str, dict]:
    return {p["item_id"]: p for p in slot["proposals"]}


def _normalize_entry(entry: Any, known: dict[str, dict], warnings: list[str]) -> dict | None:
    """A section entry is an item_id or {title, meta, body} item_id references."""
    if isinstance(entry, str):
        entry = {"body": entry}
    if not isinstance(entry, dict):
        warnings.append("ignored a malformed section entry")
        return None
    normalized = {}
    for role in ("title", "meta", "body"):
        ref = entry.get(role)
        if ref is None:
            continue
        if not isinstance(ref, str) or ref not in known:
            warnings.append(f"ignored unknown copy reference {ref!r}")
            continue
        normalized[role] = ref
    return normalized or None


def plan_page(development: dict) -> tuple[dict, list[str], list[str]]:
    """Validated page plan, design warnings, and copy items no section placed."""
    design = development.get("sandbox_prototype_design") or {}
    slot = design.get("writer_copy")
    if not isinstance(slot, dict) or not slot.get("proposals"):
        raise IngestionError("development has no writer_copy; develop it with --from-writer first")
    known = _copy_index(slot)
    warnings: list[str] = []
    page = design.get("page") if isinstance(design.get("page"), dict) else None
    sections = []
    if page and isinstance(page.get("sections"), list):
        seen_ids = set()
        for index, section in enumerate(page["sections"]):
            if not isinstance(section, dict):
                warnings.append(f"ignored malformed section {index}")
                continue
            section_id = section.get("id") if isinstance(section.get("id"), str) else ""
            if not _SLUG.match(section_id) or section_id in seen_ids:
                section_id = f"section-{index + 1}"
            seen_ids.add(section_id)
            layout = section.get("layout") if section.get("layout") in LAYOUTS else "text"
            entries = [
                e
                for e in (_normalize_entry(x, known, warnings) for x in section.get("items") or [])
                if e
            ]
            if not entries:
                warnings.append(f"section {section_id} has no valid copy and was dropped")
                continue
            heading = section.get("heading") if isinstance(section.get("heading"), str) else ""
            sections.append(
                {"id": section_id, "heading": heading[:200], "layout": layout, "entries": entries}
            )
        title = page.get("title") if isinstance(page.get("title"), str) else ""
    else:
        warnings.append("no page design supplied; rendered copy in Writer order")
        title = ""
        for index, item_id in enumerate(known):
            sections.append(
                {
                    "id": f"section-{index + 1}",
                    "heading": "",
                    "layout": "hero" if index == 0 else "text",
                    "entries": [{"body": item_id}],
                }
            )
    placed = {ref for s in sections for e in s["entries"] for ref in e.values()}
    unplaced = [item_id for item_id in known if item_id not in placed]
    if unplaced:
        sections.append(
            {
                "id": "unplaced-copy",
                "heading": "Additional copy",
                "layout": "list",
                "entries": [{"body": item_id} for item_id in unplaced],
            }
        )
    plan = {
        "title": (title or development["idea"].get("problem_framing") or "Prototype")[:200],
        "sections": sections,
    }
    return plan, warnings, unplaced


def render_html(plan: dict, slot: dict, lineage: dict) -> str:
    known = _copy_index(slot)

    def text(ref: str) -> str:
        return _esc(known[ref]["materialized_text"])

    def attrs(ref: str) -> str:
        return f' data-copy-id="{_esc(ref)}"'

    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_esc(plan['title'])}</title>",
        '<link rel="stylesheet" href="styles.css">',
        "</head>",
        "<body>",
    ]
    hero_done = False
    body: list[str] = []
    for section in plan["sections"]:
        heading_id = f"{section['id']}-heading"
        if section["layout"] == "hero" and not hero_done:
            hero_done = True
            parts.append(f'<header class="hero" id="{section["id"]}"><div class="wrap">')
            first = True
            for entry in section["entries"]:
                for role in ("title", "meta", "body"):
                    if role not in entry:
                        continue
                    tag = "h1" if first else "p"
                    first = False
                    parts.append(f"<{tag}{attrs(entry[role])}>{text(entry[role])}</{tag}>")
            parts.append("</div></header>")
            continue
        body.append(
            f'<section id="{section["id"]}" aria-labelledby="{heading_id}"><div class="wrap">'
        )
        heading = section["heading"] or section["id"].replace("-", " ").title()
        body.append(f'<h2 id="{heading_id}">{_esc(heading)}</h2>')
        if section["layout"] == "cards":
            body.append('<ul class="cards">')
            for entry in section["entries"]:
                body.append('<li class="card">')
                if "title" in entry:
                    body.append(f"<h3{attrs(entry['title'])}>{text(entry['title'])}</h3>")
                if "meta" in entry:
                    body.append(f'<p class="meta"{attrs(entry["meta"])}>{text(entry["meta"])}</p>')
                if "body" in entry:
                    body.append(f"<p{attrs(entry['body'])}>{text(entry['body'])}</p>")
                body.append("</li>")
            body.append("</ul>")
        elif section["layout"] == "list":
            body.append('<ul class="list">')
            for entry in section["entries"]:
                refs = [entry[r] for r in ("title", "meta", "body") if r in entry]
                body.append(
                    "<li>" + " ".join(f"<span{attrs(r)}>{text(r)}</span>" for r in refs) + "</li>"
                )
            body.append("</ul>")
        else:
            for entry in section["entries"]:
                for role in ("title", "meta", "body"):
                    if role in entry:
                        tag = "h3" if role == "title" else "p"
                        body.append(f"<{tag}{attrs(entry[role])}>{text(entry[role])}</{tag}>")
        body.append("</div></section>")
    parts.append("<main>")
    parts.extend(body)
    parts.append("</main>")
    parts.append(
        '<footer><div class="wrap">Prototype materialized by HowlCreate from HowlWriter proposal '
        f"{_esc(lineage.get('writer_proposal_id') or 'n/a')} "
        f"(source {_esc(lineage.get('source_idea_id') or 'n/a')}). Advisory sandbox artifact."
        "</div></footer>"
    )
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)


def render_design_notes(development: dict, warnings: list[str]) -> str:
    lines = [
        "# Design notes",
        "",
        "Advisory. Not executed, not deployed.",
        "",
        "## Architecture proposal",
        "",
        development.get("architecture_proposal", ""),
        "",
        "## Proposed tests (not executed)",
        "",
    ]
    for test in development.get("test_specification") or []:
        assertion = (
            test.get("assertion") or test.get("description") or json.dumps(test, sort_keys=True)
        )
        lines.append(f"- {assertion}")
    if warnings:
        lines += ["", "## Materialization warnings", ""] + [f"- {w}" for w in warnings]
    return "\n".join(lines) + "\n"


def materialize(
    development: dict,
    output_dir: str,
    *,
    allow_repo: bool = False,
    replace: bool = False,
    now: datetime | None = None,
) -> dict:
    """Write the prototype and its manifest into an explicit sandbox root."""
    if not isinstance(development, dict):
        raise IngestionError("creative package must be a development_result object")
    validate_envelope(development, "howl.development_result.v1")
    if development.get("authority") != {"type": "ADVISORY", "executable": False}:
        raise IngestionError("creative package requires advisory, non-executable authority")
    plan, warnings, unplaced = plan_page(development)
    slot = development["sandbox_prototype_design"]["writer_copy"]
    lineage = development.get("lineage") or {}
    copy_doc = {
        "writer_proposal_id": slot["writer_proposal_id"],
        "items": [
            {
                k: p[k]
                for k in (
                    "item_id",
                    "proposal_item_id",
                    "materialized_text",
                    "factual_status",
                    "usable",
                    "origin",
                    "evidence_refs",
                )
            }
            for p in slot["proposals"]
        ],
    }
    files = {
        "index.html": render_html(plan, slot, lineage),
        "styles.css": STYLESHEET,
        "copy.json": json.dumps(copy_doc, indent=2, ensure_ascii=False) + "\n",
        "DESIGN.md": render_design_notes(development, warnings),
    }
    sandbox = SandboxRoot(output_dir, allow_repo=allow_repo, replace=replace)
    timestamp = (now or datetime.now(UTC)).isoformat()
    provenance = development.get("provenance") or {}
    execution = provenance.get("execution") or {}
    design_inference = bool(execution.get("inference_occurred"))
    create_run_id = development["development_id"]
    dream_ids = [lineage["dream_source_id"]] if lineage.get("dream_source_id") else []
    writer_ids = [slot["writer_proposal_id"]]
    artifacts = []
    for name, content in files.items():
        data = content.encode("utf-8")
        sandbox.write(name, data)
        digest = hashlib.sha256(data).hexdigest()
        suffix = name[name.rfind(".") :]
        artifacts.append(
            {
                "artifact_id": f"art-{digest[:12]}",
                "path": name,
                "sha256": digest,
                "bytes": len(data),
                "media_type": _MEDIA.get(suffix, "application/octet-stream"),
                "create_run_id": create_run_id,
                "source_dream_ids": dream_ids,
                "source_writer_ids": writer_ids,
                # Rendering itself never calls a model; design-time inference is reported below.
                "provider": None,
                "model": None,
                "generated_at": timestamp,
            }
        )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "materialization_id": f"mat-{uuid4().hex[:12]}",
        "create_run_id": create_run_id,
        "created_at": timestamp,
        "output_dir": str(sandbox.path),
        "source_dream_ids": dream_ids,
        "source_idea_id": lineage.get("source_idea_id"),
        "source_run_id": lineage.get("source_run_id"),
        "source_writer_ids": writer_ids,
        "writer_request_id": slot.get("writer_request_id"),
        "design": {
            "development_method": provenance.get("development_method"),
            "inference_occurred": design_inference,
            "provider": execution.get("actual_provider") if design_inference else None,
            "model": execution.get("model") if design_inference else None,
            "page_designed_by_model": isinstance(
                development["sandbox_prototype_design"].get("page"), dict
            )
            and design_inference,
        },
        "materialization": {"deterministic": True, "inference_occurred": False},
        # Page title and section headings are layout labels from the design,
        # not Writer copy; they are listed so no reader credits them to Writer.
        "design_authored_text": [plan["title"]]
        + [s["heading"] for s in plan["sections"] if s["heading"]],
        "withheld_item_ids": slot.get("withheld_item_ids", []),
        "unplaced_item_ids": unplaced,
        "design_warnings": warnings,
        "artifacts": artifacts,
        "contribution": {"component": "howlcreate", "operation": "MATERIALIZED"},
        "authority": {"type": "ADVISORY", "executable": False},
    }
    sandbox.write(MANIFEST_NAME, (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    return manifest
