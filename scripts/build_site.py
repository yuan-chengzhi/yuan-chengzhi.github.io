#!/usr/bin/env python3
"""Build a bilingual, JS-optional static site using only the Python standard library.

Edit data/content.{en,zh-CN}.json and cv/source.md, then run this script.
The SVG paths and node rectangles share ONE geometry source; never hand-edit paths.
"""
from __future__ import annotations
import argparse
import difflib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'zh-CN')
COLORS = {'rust': '#a65039', 'teal': '#216f69', 'navy': '#263c58', 'blue': '#526c88'}
# x, width. Rows are parallel research relationships, not chronological stages.
COLUMNS = ((24, 226), (294, 230), (576, 272))
ROW_Y = (68, 196, 324, 452)
NODE_H = 86
FUTURE = (928, 191, 208, 260)
NAV_IDS = ('work', 'papers', 'map', 'questions', 'about')
E = lambda value: html.escape(str(value), quote=True)

def load(lang: str) -> dict:
    data = json.loads((ROOT / 'data' / f'content.{lang}.json').read_text(encoding='utf-8'))
    if data['lang'] != lang:
        raise ValueError('Locale mismatch')
    ids = [p['id'] for p in data['projects']]
    if len(ids) != 4 or len(ids) != len(set(ids)) or len(data['map_rows']) != 4:
        raise ValueError('The selected-work map needs exactly four unique rows')
    for item in data['projects'] + data['map_rows']:
        if item['tone'] not in COLORS:
            raise ValueError('Unknown map tone')
    for row in data['map_rows']:
        if row['project'] not in ids:
            raise ValueError('Map refers to an unknown project')
    return data

def graph_geometry(data: dict) -> tuple[dict, list]:
    """All edge endpoints lie on explicit rectangular boundary ports."""
    nodes, edges = {}, []
    for i, row in enumerate(data['map_rows']):
        for col, field in enumerate(('question', 'experiment', 'evidence')):
            x, width = COLUMNS[col]
            key = f"{row['id']}-{field}"
            nodes[key] = (x, ROW_Y[i], width, NODE_H)
        for source, target in (('question', 'experiment'), ('experiment', 'evidence')):
            a, b = f"{row['id']}-{source}", f"{row['id']}-{target}"
            ax, ay, aw, ah = nodes[a]
            bx, by, bw, bh = nodes[b]
            edges.append({'row': row['id'], 'from': a, 'to': b, 'kind': 'record',
                          'start': (ax + aw, ay + ah / 2), 'end': (bx, by + bh / 2)})
        ex, ey, ew, eh = nodes[f"{row['id']}-evidence"]
        fx, fy, fw, fh = FUTURE
        edges.append({'row': row['id'], 'from': f"{row['id']}-evidence", 'to': 'future',
                      'kind': 'direction', 'start': (ex + ew, ey + eh / 2),
                      'end': (fx, fy + fh * (i + 1) / 5)})
    nodes['future'] = FUTURE
    return nodes, edges

GRAPH_CSS = '''
text{font-family:system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC",sans-serif;fill:#172333}
.map-heading{font-size:12px;letter-spacing:.6px;fill:#526172}
.map-edge{fill:none;stroke:#829591;stroke-width:1.6}
.map-edge.direction{stroke:#8291a4;stroke-dasharray:5 5}
.map-node{text-decoration:none;cursor:pointer}
.map-node rect{fill:#fff;stroke:#cbd5d2;stroke-width:1.2}
.map-node .node-title{font-size:15px;font-weight:600}
.map-node .node-subtitle{font-size:12.5px;fill:#526172}
.map-node.question rect{fill:#f6f8f5}
.map-node.question text{font-size:14px;font-weight:500}
.map-node.experiment rect{fill:#f0f5f2;stroke:var(--tone)}
.map-node.experiment .node-title{font-size:16px;fill:var(--tone)}
.map-node:hover rect,.map-node:focus-visible rect{stroke:#914632;stroke-width:2.4}
.map-node:focus-visible{outline:none}
.map-node.is-active rect{stroke:#914632;stroke-width:2.4}
.map-edge.is-active{stroke:#914632;stroke-width:2.2}
.future rect{fill:#f4f6f8;stroke:#63758b;stroke-dasharray:5 4}
.future .future-title{font-size:21px;font-weight:600}
.future .future-small{font-size:12.5px;fill:#526172}
.campaign-label{font-size:10px;fill:#526172}
'''.strip()

def render_graph(data: dict, standalone: bool = False) -> str:
    lang = data['lang']
    prefix = f'map-{lang}'
    target_prefix = ('../zh/' if lang == 'zh-CN' else '../') if standalone else ''
    target_attr = ' target="_top"' if standalone else ''
    nodes, edges = graph_geometry(data)
    out = [f'<svg class="research-map" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 570" role="group" aria-labelledby="{prefix}-title {prefix}-desc" lang="{lang}">',
           f'<title id="{prefix}-title">{E(data["map_title"])}</title>',
           f'<desc id="{prefix}-desc">{E(data["map_caption"])}</desc>',
           f'<style>{GRAPH_CSS}</style>',
           '<defs>']
    for kind, color in (('record', '#829591'), ('direction', '#8291a4')):
        out.append(f'<marker id="{prefix}-{kind}" viewBox="0 0 10 8" refX="10" refY="4" markerWidth="8" markerHeight="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0L10 4L0 8Z" fill="{color}"/></marker>')
    out += ['</defs>', '<rect x="282" y="180" width="254" height="246" rx="14" fill="#eaf0ec"/>',
            f'<text class="campaign-label" x="409" y="309" text-anchor="middle">{E(data["map_group"])}</text>']
    for i, heading in enumerate(data['map_headers']):
        x = COLUMNS[i][0] if i < 3 else FUTURE[0]
        out.append(f'<text class="map-heading" x="{x}" y="34">{E(heading)}</text>')
    for edge in edges:
        sx, sy = edge['start']; ex, ey = edge['end']
        dx = (ex - sx) * .5
        path = f'M{sx:g} {sy:g} C{sx+dx:g} {sy:g} {ex-dx:g} {ey:g} {ex:g} {ey:g}'
        out.append(f'<path class="map-edge {edge["kind"]}" data-row="{edge["row"]}" data-from="{edge["from"]}" data-to="{edge["to"]}" d="{path}" marker-end="url(#{prefix}-{edge["kind"]})"/>')
    for row in data['map_rows']:
        for field in ('question', 'experiment', 'evidence'):
            key = f"{row['id']}-{field}"
            x, y, w, h = nodes[key]
            anchor = ('evidence-' if field == 'evidence' else '') + row['project']
            lines = row[field]
            label = ' · '.join(lines)
            out += [f'<a class="map-node {field}" data-node="{key}" data-row="{row["id"]}" style="--tone:{COLORS[row["tone"]]}" href="{target_prefix}#{anchor}"{target_attr} aria-label="{E(label)}">',
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>',
                    f'<text class="node-title" x="{x+w/2:g}" y="{y+36:g}" text-anchor="middle">{E(lines[0])}</text>',
                    f'<text class="node-subtitle" x="{x+w/2:g}" y="{y+59:g}" text-anchor="middle">{E(lines[1])}</text>', '</a>']
    x, y, w, h = FUTURE
    out += [f'<a class="map-node future" data-node="future" href="{target_prefix}#questions"{target_attr} aria-label="{E(" ".join(data["map_future"]))}">',
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>']
    for i, text in enumerate(data['map_future']):
        out.append(f'<text class="future-title" x="{x+w/2:g}" y="{y+67+i*30}" text-anchor="middle">{E(text)}</text>')
    for i, text in enumerate(data['map_future_sub']):
        out.append(f'<text class="future-small" x="{x+w/2:g}" y="{y+151+i*23}" text-anchor="middle">{E(text)}</text>')
    out += [f'<text class="future-small" x="{x+w/2:g}" y="{y+224}" text-anchor="middle">{E(data["map_future_status"])}</text>', '</a>', '</svg>']
    return '\n'.join(out)

def section_heading(number: str, title: str, intro: str, ident: str) -> str:
    return f'<div class="section-heading"><div><p class="eyebrow">{number}</p><h2 id="{ident}">{E(title)}</h2></div><p class="section-intro">{E(intro)}</p></div>'

def render_project(project: dict, data: dict) -> str:
    alias = '<span class="anchor-alias" id="project-tools"></span>' if project['id'] == 'project-putnam' else ''
    details = ''.join(f'<p>{E(paragraph)}</p>' for paragraph in project['details'])
    output = f'<a href="#{project["paper"]}">{E(data["output_label"])} ↗</a>' if project['paper'] else ''
    return f'''<article class="project-card tone-{project['tone']}" id="{project['id']}">
{alias}<div class="project-top"><span class="project-type">{E(project['type'])}</span><span class="project-status">{E(project['status'])}</span></div>
<h3>{E(project['title'])}</h3>
<p class="project-question">{E(project['question'])}</p>
<h4 class="project-label">{E(data['contribution_label'])}</h4><p>{E(project['contribution'])}</p>
<div class="project-evidence" id="evidence-{project['id']}"><h4 class="project-label">{E(data['evidence_label'])}</h4><p>{E(project['evidence'])}</p></div>
<details><summary>{E(data['details_label'])}</summary><div class="details-body">{details}</div></details>
<div class="project-foot"><span>{E(project['footer'])}</span>{output}</div></article>'''

def render_page(data: dict) -> str:
    lang = data['lang']; zh = lang == 'zh-CN'; base = '../' if zh else './'
    canonical = 'https://yuan-chengzhi.github.io/' + ('zh/' if zh else '')
    nav = ''.join(f'<a href="#{i}">{E(label)}</a>' for i, label in zip(NAV_IDS, data['nav']))
    tags = ''.join(f'<span>{E(t)}</span>' for t in data['tags'])
    projects = '\n'.join(render_project(p, data) for p in data['projects'])
    papers = '\n'.join(f'''<article class="paper" id="{p['id']}"><div class="paper-meta"><span>{E(p['venue'])}</span><span>{E(p['role'])}</span></div><h3 lang="en">{E(p['title'])}</h3><p>{E(p['scope'])} <a href="#{p['project']}">{E(data['contribution_link'])} ↗</a></p></article>''' for p in data['papers'])
    mobile_rows = '\n'.join(f'''<li class="map-text-row tone-{r['tone']}"><p class="map-text-question">{E(' '.join(r['question']))}</p><a href="#{r['project']}">{E(' · '.join(r['experiment']))} ↗</a><p class="map-text-result"><span aria-hidden="true">↓</span> {E(' · '.join(r['evidence']))}</p></li>''' for r in data['map_rows'])
    horizon = '\n'.join(f'''<article class="direction-card" id="{p['id']}"><p class="direction-index">0{i+1}</p><h3>{E(p['title'])}</h3><p class="direction-question">{E(p['question'])}</p><p>{E(p['body'])}</p></article>''' for i, p in enumerate(data['horizon']))
    notes = '\n'.join(f'''<article class="exploration" id="{n['id']}"><div><p class="eyebrow">{E(n['status'])}</p><h3>{E(n['title'])}</h3></div><p>{E(n['text'])}</p></article>''' for n in data['notes'])
    methods = ''.join(f'<li>{E(line)}</li>' for line in data['methods'])
    return f'''<!doctype html>
<!-- Generated by scripts/build_site.py. Edit data/content.{lang}.json instead. -->
<html lang="{lang}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(data['title'])}</title><meta name="description" content="{E(data['description'])}">
<meta property="og:title" content="{E(data['title'])}"><meta property="og:description" content="{E(data['description'])}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
<meta property="og:locale" content="{'zh_CN' if zh else 'en_US'}"><meta property="og:locale:alternate" content="{'en_US' if zh else 'zh_CN'}">
<link rel="canonical" href="{canonical}"><link rel="alternate" hreflang="en" href="https://yuan-chengzhi.github.io/"><link rel="alternate" hreflang="zh-CN" href="https://yuan-chengzhi.github.io/zh/"><link rel="alternate" hreflang="x-default" href="https://yuan-chengzhi.github.io/">
<link rel="stylesheet" href="{base}styles.css?v=3"><script defer src="{base}site.js?v=3"></script>
</head><body>
<a class="skip-link" href="#main-content">{E(data['skip'])}</a>
<header class="site-header"><div class="shell header-inner"><a class="wordmark" href="./" aria-label="{E(data['name'])}"><span class="wordmark-mark" aria-hidden="true">CY</span><span class="wordmark-text">{E(data['wordmark'])}</span></a><nav aria-label="{E(data['nav_label'])}">{nav}<a class="language-switch" href="{data['language_href']}" lang="{'en' if zh else 'zh-CN'}" hreflang="{'en' if zh else 'zh-CN'}">{E(data['language'])}</a></nav></div></header>
<main id="main-content">
<section class="hero shell" aria-labelledby="hero-title"><div class="hero-copy"><p class="eyebrow">{E(data['eyebrow'])}</p><h1 id="hero-title">{E(data['name'])}<span class="other-name" lang="{'en' if zh else 'zh-CN'}">{E(data['other_name'])}</span></h1><p class="identity">{E(data['identity'])}</p><p class="hero-lede">{E(data['lede'])}</p><p class="hero-body">{E(data['bio'])}</p><div class="hero-actions"><a class="button button-primary" href="#work">{E(data['cta_work'])} <span aria-hidden="true">↓</span></a><a class="button button-secondary" href="{base}cv/">{E(data['cta_cv'])}</a><a class="quiet-link" href="mailto:yuanchengzhi@sjtu.edu.cn">{E(data['cta_email'])} ↗</a><a class="quiet-link" href="https://github.com/yuan-chengzhi" rel="noreferrer">GitHub ↗</a></div><div class="hero-tags">{tags}</div></div><aside class="hero-note" aria-label="{E(data['note_label'])}"><p class="note-label">{E(data['note_label'])}</p><p class="note-question">{E(data['note'])}</p><p class="note-footer"><span class="signal-dot" aria-hidden="true"></span>{E(data['note_status'])}</p></aside></section>
<section id="work" class="section section-tint" aria-labelledby="work-title"><div class="shell">{section_heading('01',data['work_title'],data['work_intro'],'work-title')}<div class="project-grid">{projects}</div></div></section>
<section id="papers" class="section shell papers-section" aria-labelledby="papers-title">{section_heading('02',data['papers_title'],data['papers_intro'],'papers-title')}<div class="papers-list">{papers}</div></section>
<section id="map" class="section shell map-section" aria-labelledby="map-title">{section_heading('03',data['map_title'],data['map_intro'],'map-title')}<figure class="map-frame"><div class="map-visual">{render_graph(data)}</div><ol class="map-text" aria-label="{E(data['map_mobile_label'])}">{mobile_rows}<li class="map-text-future"><a href="#questions">{' · '.join(E(s) for s in data['map_future'])} ↗</a><span>{E(data['map_future_status'])}</span></li></ol><figcaption class="map-caption"><p>{E(data['map_caption'])}</p><div class="map-meta"><div class="map-legend"><span><i aria-hidden="true"></i>{E(data['map_legend'][0])}</span><span><i class="dashed" aria-hidden="true"></i>{E(data['map_legend'][1])}</span></div><a href="{base}assets/research-map.{lang}.svg">{E(data['map_svg_label'])} ↗</a></div></figcaption></figure></section>
<section id="questions" class="section section-tint" aria-labelledby="horizon-title"><div class="shell"><span class="anchor-alias" id="horizon"></span><span class="anchor-alias" id="project-horizon"></span>{section_heading('04',data['horizon_title'],data['horizon_intro'],'horizon-title')}<div class="directions-grid">{horizon}</div><p class="scope-note">{E(data['horizon_note'])}</p></div></section>
<section class="section shell notes-section" aria-labelledby="notes-title"><p class="eyebrow">05</p><h2 id="notes-title">{E(data['notes_title'])}</h2>{notes}</section>
<section id="about" class="section about-section" aria-labelledby="about-title"><div class="shell about-grid"><div><p class="eyebrow">{E(data['nav'][-1])}</p><h2 id="about-title">{E(data['about_title'])}</h2></div><div class="about-copy"><p>{E(data['about_text'])}</p><p>{E(data['about_second'])}</p><h3 class="project-label">{E(data['methods_label'])}</h3><ul class="methods">{methods}</ul><div class="contact-row"><a href="mailto:yuanchengzhi@sjtu.edu.cn">yuanchengzhi@sjtu.edu.cn ↗</a><a href="https://github.com/yuan-chengzhi">GitHub ↗</a><a href="{base}cv/">{E(data['cta_cv'])} ↗</a></div><p class="public-note">{E(data['public_note'])}</p></div></div></section>
</main><footer class="site-footer"><div class="shell footer-inner"><span>{E(data['name'])} · {E(data['footer'])}</span><span>{E(data['updated'])}</span></div></footer>
</body></html>
'''

def inline_markdown(text: str) -> str:
    # Limited trusted editorial syntax, HTML always escaped first.
    text = E(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)

def render_cv() -> str:
    lines = (ROOT / 'cv' / 'source.md').read_text(encoding='utf-8').splitlines()
    body = []; in_list = False
    for line in lines:
        if not line.strip():
            continue
        if not line.startswith('- ') and in_list:
            body.append('</ul>'); in_list = False
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if not 1 <= level <= 3:
                raise ValueError('Unsupported CV heading')
            body.append(f'<h{level}>{inline_markdown(line[level:].strip())}</h{level}>')
        elif line.startswith('- '):
            if not in_list:
                body.append('<ul>'); in_list = True
            body.append(f'<li>{inline_markdown(line[2:])}</li>')
        else:
            body.append(f'<p>{inline_markdown(line)}</p>')
    if in_list:
        body.append('</ul>')
    return '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>袁诚志 · CV</title><meta name="description" content="袁诚志的中文学术简历。数学与人工智能、多智能体系统与形式化证明研究。"><link rel="stylesheet" href="../styles.css?v=3"><script defer src="../site.js?v=3"></script></head><body class="cv-page"><a class="skip-link" href="#cv-content">跳转到简历</a><header class="cv-toolbar"><a href="../zh/">← 中文主页</a><a href="../">English homepage</a><a href="source.md" download>Markdown</a><button type="button" data-print hidden>打印 / 另存为 PDF</button></header><main class="cv-sheet" id="cv-content">''' + '\n'.join(body) + '</main></body></html>\n'

def outputs() -> dict[Path, str]:
    results = {}
    data = [load(lang) for lang in LANGUAGES]
    for key in ('projects', 'papers', 'horizon', 'notes', 'map_rows'):
        if [x['id'] for x in data[0][key]] != [x['id'] for x in data[1][key]]:
            raise ValueError(f'Bilingual IDs differ in {key}')
    for locale in data:
        page = 'zh/index.html' if locale['lang'] == 'zh-CN' else 'index.html'
        results[ROOT / page] = render_page(locale)
        results[ROOT / 'assets' / f"research-map.{locale['lang']}.svg"] = render_graph(locale, standalone=True) + '\n'
    results[ROOT / 'cv' / 'index.html'] = render_cv()
    return results

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail on stale generated files without changing them')
    args = parser.parse_args(); stale = []
    for path, content in outputs().items():
        previous = path.read_text(encoding='utf-8') if path.exists() else ''
        if args.check:
            if previous != content:
                stale.append(str(path.relative_to(ROOT)))
                print(''.join(difflib.unified_diff(previous.splitlines(True), content.splitlines(True), fromfile=str(path), tofile='generated'))[:2500])
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            print(f'Built {path.relative_to(ROOT)}')
    if stale:
        print('Stale output: ' + ', '.join(stale)); return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
