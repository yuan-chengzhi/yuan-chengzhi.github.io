# Chengzhi Yuan · Research homepage

Bilingual, dependency-free static site: English at `/`, Chinese at `/zh/`, and a
printable Chinese CV at `/cv/`. Existing research anchors remain usable.

## Edit and build

Edit `data/content.en.json` and `data/content.zh-CN.json`, then run:

```sh
python3 scripts/build_site.py
python3 scripts/build_site.py --check
python3 -m unittest discover -s tests -v
node --check site.js
python3 -m http.server 8000
```

Open `http://localhost:8000/` or `http://localhost:8000/zh/`.
Commit both the editorial sources and generated HTML/SVG. GitHub Pages can keep
serving the repository root; no framework, package install, or publishing-mode
change is required. Do not hand-edit generated pages.

The two locale files replace the previous separate project/map/horizon JSON
files. Project, paper, and direction IDs must match across languages. The build
rejects mismatches. No content depends on runtime JSON requests: even without
JavaScript, both pages contain all cards, papers, details, and map alternatives.

## Research map

`graph_geometry()` in `scripts/build_site.py` is the single layout source. It
computes paths from the same rectangles that render the nodes, using right/left
boundary ports and ordered ports for the future-direction node. Marker tips end
at those ports. Hover/focus changes stroke emphasis only, never node size or
position. The tests check endpoints and collisions with unrelated nodes.

The map is relational, not chronological or causal. Two entries are grouped as
branches of the same FLT project. Solid edges link questions, work, and recorded
results; dashed edges motivate a direction that has not yet been demonstrated.
On small screens the SVG is replaced by a readable HTML relation list—not a
shrunk or horizontally scrolling desktop graphic. Standalone SVGs are generated
in `assets/` with working links back to the appropriate language edition.

## CV and public scope

`cv/source.md` is the editable, user-confirmed Chinese CV. The generated page has
print styles and a Print / Save as PDF button; native browser print also works
without JavaScript. This is an HTML CV, not a link to an unhosted PDF. Only the
user-approved CV and public-facing summaries belong here. Do not upload raw
experiment logs, private manuscript PDFs, credentials, or private project code.
Both manuscript entries remain **submitted, third author**. Code visibility is
not changed by this site update.

`site.js` only preserves the current section on language switches, highlights
related SVG nodes, and exposes the print button. It does not render content.
