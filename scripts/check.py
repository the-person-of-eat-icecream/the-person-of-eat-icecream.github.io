"""Check generated pages for broken local assets, links, fragments and feed XML."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
CONFIG = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
BASE = urlparse(os.environ.get('SITE_URL') or CONFIG['url']).path.rstrip('/')


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = set()
        self.links = []
        self.h1_count = 0
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'h1':
            self.h1_count += 1
        if attrs.get('id'):
            assert attrs['id'] not in self.ids, f'{self.path}: duplicate id {attrs["id"]}'
            self.ids.add(attrs['id'])
        for attr in ('href', 'src'):
            if attrs.get(attr):
                self.links.append(attrs[attr])


documents = {path.resolve(): Document(path) for path in OUT.rglob('*.html')}
assert documents, 'Build the site first'
checked = 0
for source, document in documents.items():
    assert document.h1_count == 1, f'{source}: expected exactly one h1'
    assert 'main' in document.ids, f'{source}: missing main content anchor'
    for link in document.links:
        parsed = urlparse(link)
        if parsed.scheme or parsed.netloc:
            continue
        target_path = unquote(parsed.path)
        if not target_path:
            target = source
        elif target_path.startswith('/'):
            assert not BASE or target_path.startswith(BASE + '/'), f'{source}: link omits site base path: {link}'
            target = OUT / target_path[len(BASE):].lstrip('/')
        else:
            target = source.parent / target_path
        if target.is_dir():
            target = target / 'index.html'
        target = target.resolve()
        assert target.is_relative_to(OUT.resolve()), f'{source}: link escapes site directory: {link}'
        assert target.is_file(), f'{source}: missing target: {link}'
        if parsed.fragment and target in documents:
            assert unquote(parsed.fragment) in documents[target].ids, f'{source}: missing fragment: {link}'
        checked += 1

rss = ET.parse(OUT / 'feed.xml')
items = rss.findall('./channel/item')
assert items, 'RSS must include published posts'
assert len({item.findtext('guid') for item in items}) == len(items), 'Duplicate RSS identifiers'
for item in items:
    assert item.findtext('title') and item.findtext('link') and item.findtext('pubDate'), 'Incomplete RSS item'
sitemap = ET.parse(OUT / 'sitemap.xml')
assert sitemap.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'), 'Empty sitemap'
assert (OUT / '.nojekyll').is_file(), 'Missing .nojekyll'
print(f'PASS: {len(documents)} HTML pages, {checked} internal links/assets/fragments, RSS and sitemap XML')
