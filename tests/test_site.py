"""Offline regression checks: run `python -m unittest discover -s tests -v`."""
from __future__ import annotations
import importlib.util
import math
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_site', ROOT / 'scripts/build_site.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
NS = {'s': 'http://www.w3.org/2000/svg'}

class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.ids=[]; self.links=[]; self.resources=[]; self.classes=[]; self.words=[]
        self.feed(source)
    def handle_starttag(self, tag, attributes):
        a=dict(attributes)
        if 'id' in a: self.ids.append(a['id'])
        self.classes.extend(a.get('class','').split())
        if tag=='a' and 'href' in a: self.links.append(a['href'])
        if tag=='script' and 'src' in a: self.resources.append(a['src'])
        if tag=='link' and a.get('rel')=='stylesheet': self.resources.append(a['href'])
    def handle_data(self, text): self.words.append(text)

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.en=build.load('en'); cls.zh=build.load('zh-CN')
        cls.outputs=build.outputs()
    def test_generated_files_current(self):
        for path, content in self.outputs.items():
            with self.subTest(file=path): self.assertEqual(path.read_text(), content)
    def test_language_ids_match(self):
        for key in ('projects','papers','notes','horizon','map_rows'):
            self.assertEqual([x['id'] for x in self.en[key]], [x['id'] for x in self.zh[key]])
    def test_language_graph_geometry_identical(self):
        self.assertEqual(build.graph_geometry(self.en), build.graph_geometry(self.zh))
    def test_no_duplicate_ids(self):
        for path, content in self.outputs.items():
            if path.suffix=='.html':
                doc=Document(content)
                self.assertEqual(len(doc.ids),len(set(doc.ids)),str(path))
    def test_internal_links_and_resources_exist(self):
        for path, source in self.outputs.items():
            if path.suffix!='.html': continue
            doc=Document(source)
            for link in doc.links+doc.resources:
                url=urlsplit(link)
                if url.scheme or url.netloc: continue
                target=(path.parent/unquote(url.path)).resolve() if url.path else path
                if target.is_dir(): target=target/'index.html'
                with self.subTest(path=path.name,link=link):
                    self.assertTrue(target.exists(),str(target))
                    if url.fragment and target.suffix=='.html':
                        self.assertIn(unquote(url.fragment),Document(target.read_text()).ids)
    def test_legacy_anchors_preserved(self):
        for name in ('index.html','zh/index.html'):
            ids=Document((ROOT/name).read_text()).ids
            for anchor in ('map','work','questions','horizon','about','project-tools','project-horizon','project-putnam','project-flt','project-traces'):
                self.assertIn(anchor,ids)
    def test_cards_present_without_javascript(self):
        for name in ('index.html','zh/index.html'):
            doc=Document((ROOT/name).read_text())
            self.assertEqual(doc.classes.count('project-card'),4)
            self.assertEqual(doc.classes.count('paper'),2)
            self.assertEqual(doc.classes.count('direction-card'),3)
            self.assertNotIn('enable JavaScript',' '.join(doc.words))
    def test_publication_status_and_rank(self):
        for data in (self.en,self.zh):
            self.assertEqual(len(data['papers']),2)
            for paper in data['papers']:
                self.assertIn(paper['role'], ('Third author','第三作者'))
                self.assertTrue('Submitted' in paper['venue'] or '投稿' in paper['venue'])
    def test_result_boundaries_are_retained(self):
        text=' '.join(Document((ROOT/'index.html').read_text()).words)
        for claim in ('internal final_verified','not an official Putnam result','8 parallel attempts','recorded times totaling about 5.5 hours','full FLT target remains unfinished','aggregate agent-hours','not an implemented self-evolving system'):
            self.assertIn(claim,text)
    def test_no_private_repository_or_manuscript_links(self):
        for name in ('index.html','zh/index.html','cv/index.html'):
            links=Document((ROOT/name).read_text()).links
            for link in links:
                self.assertNotIn('Researching-Research',link)
                self.assertNotIn('openreview.net',link)
                self.assertNotIn('/nustarai/',link)
    def test_graph_counts_and_endpoint_ports(self):
        for data in (self.en,self.zh):
            nodes,edges=build.graph_geometry(data)
            self.assertEqual(len(nodes),13); self.assertEqual(len(edges),12)
            for edge in edges:
                ax,ay,aw,ah=nodes[edge['from']]; bx,by,bw,bh=nodes[edge['to']]
                sx,sy=edge['start']; ex,ey=edge['end']
                self.assertAlmostEqual(sx,ax+aw); self.assertAlmostEqual(ex,bx)
                self.assertTrue(ay<sy<ay+ah); self.assertTrue(by<ey<by+bh)
                self.assertGreater(ex,sx)
    def test_curves_do_not_cross_unrelated_nodes(self):
        nodes,edges=build.graph_geometry(self.en)
        for edge in edges:
            sx,sy=edge['start']; ex,ey=edge['end']; d=(ex-sx)/2
            for step in range(1,100):
                t=step/100; u=1-t
                x=u**3*sx+3*u*u*t*(sx+d)+3*u*t*t*(ex-d)+t**3*ex
                y=u**3*sy+3*u*u*t*sy+3*u*t*t*ey+t**3*ey
                for name,(nx,ny,w,h) in nodes.items():
                    if name in (edge['from'],edge['to']): continue
                    self.assertFalse(nx<x<nx+w and ny<y<ny+h,(edge,name))
    def test_svg_valid_and_standalone_links_resolve(self):
        for data in (self.en,self.zh):
            path=ROOT/'assets'/f"research-map.{data['lang']}.svg"
            svg=ET.fromstring(path.read_text())
            self.assertEqual(svg.get('viewBox'),'0 0 1160 570')
            self.assertEqual(len(svg.findall('.//s:a',NS)),13)
            for marker in svg.findall('.//s:marker',NS):
                self.assertEqual(marker.get('refX'),'10')
            for link in svg.findall('.//s:a',NS):
                url=urlsplit(link.get('href')); target=(path.parent/url.path).resolve()/'index.html'
                self.assertIn(url.fragment,Document(target.read_text()).ids)
    def test_hover_cannot_move_nodes_off_their_ports(self):
        self.assertNotIn('transform:',build.GRAPH_CSS)
        self.assertNotIn('scale(',build.GRAPH_CSS)
    def test_cv_source_is_present_and_escaped(self):
        self.assertTrue((ROOT/'cv/source.md').is_file())
        self.assertEqual(build.inline_markdown('<script>x</script>'),'&lt;script&gt;x&lt;/script&gt;')
        self.assertIn('第三作者',(ROOT/'cv/index.html').read_text())

if __name__=='__main__': unittest.main()
