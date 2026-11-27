"""Build the blog into dist/. Run from any working directory with Python 3.12+."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timezone
from email.utils import format_datetime
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
CONFIG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
SITE_URL = (os.environ.get("SITE_URL") or CONFIG["url"]).rstrip("/")
parsed_url = urlparse(SITE_URL)
if parsed_url.scheme not in {"https", "http"} or not parsed_url.netloc or parsed_url.query or parsed_url.fragment:
    raise ValueError("SITE_URL must be an absolute HTTP(S) URL without a query or fragment")
BASE = parsed_url.path.rstrip("/")


def esc(value):
    return escape(str(value), quote=True)


def url(path=""):
    return f"{BASE}/{path.lstrip('/')}"


def absolute(path=""):
    return f"{SITE_URL}/{path.lstrip('/')}"


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(html):
    parser = PlainText()
    parser.feed(html)
    return " ".join(parser.parts)


def read_posts():
    posts = []
    for source in sorted((ROOT / "content").glob("*.md")):
        text = source.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"{source.name}: missing metadata block")
        metadata, body = text[4:].split("\n---\n", 1)
        info = {}
        for line in metadata.splitlines():
            if not line.strip():
                continue
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
        for key in ("title", "date", "category", "summary"):
            if not info.get(key):
                raise ValueError(f"{source.name}: missing {key}")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", source.stem):
            raise ValueError(f"{source.name}: use lowercase letters, numbers and hyphens in filenames")
        published = date.fromisoformat(info["date"])
        md = markdown.Markdown(extensions=["extra", "toc", "sane_lists"], extension_configs={
            "toc": {"permalink": False, "toc_depth": "2-2"}
        })
        rendered = md.convert(body)
        text_content = plain(rendered)
        info.update(slug=source.stem, html=rendered, toc=md.toc.replace('class="toc"', 'class="toc-list"'),
                    date_obj=published, path=f"posts/{source.stem}/",
                    minutes=max(1, round(len(text_content) / 350)),
                    search=f"{info['title']} {info['summary']} {info['category']} {text_content}",
                    featured=info.get("featured", "false").lower() == "true")
        posts.append(info)
    if not posts:
        raise ValueError("Add at least one Markdown post to content/")
    return sorted(posts, key=lambda post: (post["date"], post["slug"]), reverse=True)


POSTS = read_posts()
CATEGORIES = Counter(post["category"] for post in POSTS)

THEME_INIT = """try{document.documentElement.dataset.theme=localStorage.getItem('quiet-notes-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}catch{document.documentElement.dataset.theme='light'}"""
SEARCH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>'
THEME_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M20 13A8 8 0 0 1 11 4a8.5 8.5 0 1 0 9 9Z"/></svg>'
HERO_ART = '<svg viewBox="0 0 270 220" fill="none" aria-hidden="true"><circle cx="135" cy="105" r="75" stroke="currentColor" stroke-opacity=".12"/><circle cx="135" cy="105" r="56" stroke="currentColor" stroke-opacity=".15"/><path d="M17 155C50 155 59 61 98 61s21 117 65 117 50-106 90-106" stroke="currentColor" stroke-width="1.3"/><path d="M17 171C58 171 62 80 101 80s24 115 65 115 49-108 88-108" stroke="currentColor" stroke-opacity=".45"/><path d="M17 140C50 140 57 43 96 43s25 115 65 115 49-106 93-106" stroke="currentColor" stroke-opacity=".25"/><circle cx="98" cy="61" r="4" fill="currentColor"/><path d="M214 25v18m-9-9h18" stroke="currentColor" stroke-opacity=".45"/><path d="M28 196h65" stroke="currentColor" stroke-opacity=".25"/><text x="164" y="215" fill="currentColor" fill-opacity=".5" font-family="Georgia, serif" font-size="11" font-style="italic">a moment to think.</text></svg>'
BOOK_ART = '<svg viewBox="0 0 200 200" fill="none" aria-hidden="true"><circle cx="100" cy="100" r="74" stroke="currentColor" stroke-opacity=".12"/><path d="M45 66c20-7 38-5 55 6 17-11 35-13 55-6v80c-20-7-38-5-55 6-17-11-35-13-55-6Z" stroke="currentColor" stroke-width="1.4"/><path d="M100 72v80M58 83c10-2 19-1 29 4m-29 10c10-2 19-1 29 4m-29 10c10-2 19-1 29 4m26-28c9-5 18-6 29-4m-29 18c9-5 18-6 29-4m-29 18c9-5 18-6 29-4" stroke="currentColor" stroke-opacity=".5"/><path d="M146 36v16m-8-8h16" stroke="currentColor" stroke-opacity=".5"/></svg>'


def header(active):
    nav = "".join(f'<a href="{url(path)}"' + (' aria-current="page"' if active == name else '') + f'>{name}</a>'
                  for name, path in [("首页", ""), ("文章", "notes/"), ("归档", "archive/"), ("关于", "about/")])
    return f'''<a class="skip-link" href="#main">跳转到正文</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" href="{url()}" aria-label="{esc(CONFIG['title'])}首页"><span class="brand-mark" aria-hidden="true">{esc(CONFIG['title'][0])}</span><span class="brand-name">{esc(CONFIG['title'])}<span class="brand-en">{esc(CONFIG['english_title'])}</span></span></a>
<nav class="nav" aria-label="主导航">{nav}<button class="theme-toggle" data-theme-toggle aria-label="切换到深色模式" aria-pressed="false">{THEME_ICON}<span>深色</span></button></nav>
</div></header>'''


def footer():
    return f'''<footer class="site-footer"><div class="wrap footer-inner"><div>© {max(post['date_obj'].year for post in POSTS)} {esc(CONFIG['author'])} <span class="footer-note"> · 记录，让想法慢慢生长。</span></div><div class="footer-links"><a href="{url('feed.xml')}">RSS 订阅</a><a href="{esc(CONFIG['github'])}">GitHub</a><a href="https://huggingface.co/spaces/lvwerra/distill-blog-template">基于 Distill</a></div></div></footer>'''


def page(title, content, active="文章", path="", description=None, post=None):
    description = description or CONFIG["description"]
    full_title = CONFIG["title"] if not title else f"{title} · {CONFIG['title']}"
    extra = ''
    if post:
        extra = f'<script src="{url("assets/vendor/distill.js")}" defer></script>'
    canonical = absolute(path)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title><meta name="description" content="{esc(description)}"><meta name="author" content="{esc(CONFIG['author'])}">
<meta property="og:title" content="{esc(full_title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="{'article' if post else 'website'}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:locale" content="zh_CN">
<link rel="canonical" href="{esc(canonical)}"><link rel="icon" type="image/svg+xml" href="{url('assets/favicon.svg')}"><link rel="alternate" type="application/rss+xml" title="{esc(CONFIG['title'])}" href="{url('feed.xml')}">
<script>{THEME_INIT}</script><link rel="stylesheet" href="{url('assets/style.css')}">{extra}<script src="{url('assets/app.js')}" defer></script></head>
<body class="blog-page">{header(active)}{content}{footer()}</body></html>'''


def post_meta(post):
    return f'<div class="post-meta"><span class="tag">{esc(post["category"])}</span><span class="separator" aria-hidden="true"></span><time datetime="{post["date"]}">{post["date"].replace("-", ".")}</time><span class="separator" aria-hidden="true"></span><span>{post["minutes"]} 分钟阅读</span></div>'


def card(post):
    return f'''<article class="post-card" data-post data-post-category="{esc(post['category'])}" data-search="{esc(post['search'])}">{post_meta(post)}<a href="{url(post['path'])}"><h3>{esc(post['title'])}</h3><p>{esc(post['summary'])}</p></a></article>'''


def sidebar():
    categories = ''.join(f'<a class="category-link" href="{url("notes/")}?category={quote(name)}#articles"><span>{esc(name)}</span><span>{count:02d}</span></a>' for name, count in CATEGORIES.items())
    return f'''<aside class="sidebar" aria-label="博客信息"><section class="sidebar-section"><div class="profile-avatar" aria-hidden="true">w.</div><h3 class="profile-name">{esc(CONFIG['author'])}</h3><p>保持好奇，慢慢记录。<br>关于学习、创造与日常。</p><a class="text-link" href="{url('about/')}">多了解一点</a></section><section class="sidebar-section"><h3>写作分类</h3>{categories}</section><section class="sidebar-section"><p class="small-label">A NOTE TO SELF</p><p class="sidebar-note">不必等想清楚了，<br>才开始写下来。</p><p>这个博客，从一点点记录开始。</p></section></aside>'''


def listing_tools():
    filters = ''.join(f'<button class="filter" data-category="{esc(category)}" aria-pressed="{str(category == "全部").lower()}">{esc(category)}</button>' for category in ['全部', *CATEGORIES])
    return f'''<div class="list-tools"><div class="filters" role="group" aria-label="按分类筛选">{filters}</div><label class="search-box">{SEARCH_ICON}<input type="search" data-search aria-label="搜索文章" placeholder="搜索文章…" autocomplete="off"></label></div><noscript><p class="noscript-notice">文章可直接阅读；搜索与筛选需要启用 JavaScript。</p></noscript>'''


def empty_state():
    return '<div class="empty" data-empty hidden><p>暂时没有找到相关的文章。</p><button data-reset-search>查看全部文章</button></div>'


def home():
    return page('你好，我是 ' + CONFIG['author'], f'''<main id="main" class="wrap personal-home">
<section class="intro-hero" aria-labelledby="intro-title"><div class="intro-copy"><div class="eyebrow">A LITTLE INTRODUCTION</div><h1 id="intro-title">你好，我是<br><em>{esc(CONFIG['author'])}。</em></h1><p class="intro-description">这里记录我的学习、创作与日常。</p><p class="intro-welcome">欢迎来到我的个人小站。</p><div class="intro-actions"><a class="intro-primary" href="{url('notes/')}">读我的文章</a><a class="intro-secondary" href="{esc(CONFIG['github'])}">在 GitHub 找到我</a></div></div><div class="intro-portrait" aria-hidden="true"><div class="intro-orbit"><span>w.</span></div><span class="intro-portrait-caption">a space of my own.</span></div></section>
<section class="intro-about" aria-labelledby="intro-about-title"><div><div class="eyebrow">ABOUT THIS SPACE</div><h2 id="intro-about-title">一点介绍，<br>一些正在生长的记录。</h2></div><div class="intro-about-copy"><p>你好，我是 {esc(CONFIG['author'])}。这里记录我的学习、创作与日常。</p><p>这个小站用来存放文字、想法，以及动手实践的过程。希望每一次记录，都能让思考变得更清晰一点。</p><a class="text-link" href="{url('about/')}">更多关于我</a></div></section>
<div class="intro-links"><section class="intro-link-card"><span class="eyebrow">WRITING</span><h2>文字与笔记</h2><p>把学习中的发现、实践的过程和日常随想，慢慢写下来。</p><a class="text-link" href="{url('notes/')}">浏览文章</a></section><section class="intro-link-card"><span class="eyebrow">ELSEWHERE</span><h2>保持联系</h2><p>你可以在 GitHub 找到我，也可以通过 RSS 订阅新的文章。</p><div class="intro-social"><a class="text-link" href="{esc(CONFIG['github'])}">GitHub</a><a class="text-link" href="{url('feed.xml')}">RSS 订阅</a></div></section></div>
</main>''', active='首页', description=f"你好，我是 {CONFIG['author']}。这里记录我的学习、创作与日常。")


def notes():
    featured = next((post for post in POSTS if post['featured']), POSTS[0])
    return page('文章与笔记', f'''<main id="main" class="wrap"><section class="hero"><div><div class="eyebrow">NOTES ON LEARNING & LIVING</div><h1>在这里，留下一点<br><em>思考的痕迹。</em></h1><p class="hero-description">{esc(CONFIG['description'])}</p><div class="hero-signature"><span class="avatar" aria-hidden="true">w.</span><span>{esc(CONFIG['author'])} 的个人博客</span></div></div><div class="hero-art">{HERO_ART}</div></section>
<section aria-label="置顶文章"><div class="section-head"><h2>值得停留</h2><span class="caption">FEATURED NOTE</span></div><a class="feature" href="{url(featured['path'])}"><div class="feature-copy">{post_meta(featured)}<h2>{esc(featured['title'])}</h2><p>{esc(featured['summary'])}</p><span class="read-label">读这篇文章</span></div><div class="feature-art">{BOOK_ART}</div></a></section>
<div class="content-layout"><section id="articles" aria-label="全部文章"><div class="section-head list-heading"><h2>最近的记录 <span>Latest notes</span></h2><span class="caption" data-result-count aria-live="polite">{len(POSTS)} 篇文章</span></div>{listing_tools()}{''.join(card(post) for post in POSTS)}{empty_state()}</section>{sidebar()}</div></main>''', path='notes/')


def archive():
    groups = []
    for year in sorted({post['date_obj'].year for post in POSTS}, reverse=True):
        groups.append(f'<h2 class="archive-year">{year}</h2>' + ''.join(card(post) for post in POSTS if post['date_obj'].year == year))
    return page('文章归档', f'''<main id="main" class="wrap"><div class="page-intro"><div class="eyebrow">THE ARCHIVE</div><h1>慢慢积累的文字。</h1><p>把每一次思考，放回它发生的时间里。共 {len(POSTS)} 篇记录。</p></div><div class="content-layout archive-layout"><section aria-label="按年归档的文章">{''.join(groups)}</section>{sidebar()}</div></main>''', active='归档', path='archive/')


def about():
    paragraphs = ''.join(f'<p>{esc(paragraph)}</p>' for paragraph in CONFIG['about'])
    return page('关于我', f'''<main id="main" class="wrap"><div class="page-intro"><div class="eyebrow">A LITTLE ABOUT ME</div><h1>关于我，也关于这里。</h1><p>屏幕的另一边，很高兴与你相遇。</p></div><div class="about-body">{paragraphs}<div class="about-card"><strong>为什么叫「{esc(CONFIG['title'])}」</strong><p>给匆忙的日常留一个停顿，让那些细小的想法，有机会成为文字。</p></div><h2>找到我</h2><p><a class="text-link" href="{esc(CONFIG['github'])}">GitHub · {esc(CONFIG['author'])}</a></p><p><a class="text-link" href="{url('feed.xml')}">通过 RSS 订阅新的文章</a></p></div></main>''', active='关于', path='about/')


def article(post, index):
    frontmatter = json.dumps({'title': post['title'], 'description': post['summary'], 'published': post['date'],
                             'authors': [{'author': CONFIG['author'], 'authorURL': CONFIG['github']}]}, ensure_ascii=False).replace('<', '\\u003c')
    next_post = POSTS[(index + 1) % len(POSTS)] if len(POSTS) > 1 else None
    next_link = '' if not next_post else f'<div class="article-next"><span>接着读一篇</span><a href="{url(next_post["path"])}">{esc(next_post["title"])}</a></div>'
    toc = f'<details class="toc" open><summary>本文目录</summary>{post["toc"]}</details>' if '<li>' in post['toc'] else ''
    return page(post['title'], f'''<div class="article-progress" data-reading-progress aria-hidden="true"></div>
<d-front-matter><script type="text/json">{frontmatter}</script></d-front-matter><main id="main" class="wrap article-main"><div class="article-top"><a class="back-link" href="{url('notes/')}#articles">返回文章列表</a><d-title><div class="eyebrow">{esc(post['category'])} · NOTE</div><h1>{esc(post['title'])}</h1><p>{esc(post['summary'])}</p></d-title><d-byline hidden></d-byline><div class="article-meta"><span>{esc(CONFIG['author'])}</span><time datetime="{post['date']}">{post['date'].replace('-', '.')}</time><span>约 {post['minutes']} 分钟阅读</span></div></div><div class="reading-layout">{toc}<d-article>{post['html']}</d-article><d-appendix><d-footnote-list></d-footnote-list><d-citation-list></d-citation-list></d-appendix><div class="article-end">写下此刻，留给以后的自己。<br><a href="{url('feed.xml')}">RSS 订阅</a> · <a href="{url('archive/')}">更多文章</a></div>{next_link}</div></main>''', path=post['path'], description=post['summary'], post=post)


def write(path, text):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')


def feed():
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for key, value in [('title', CONFIG['title']), ('link', absolute()), ('description', CONFIG['description']), ('language', 'zh-CN')]:
        ET.SubElement(channel, key).text = value
    for post in POSTS:
        item = ET.SubElement(channel, 'item')
        for key, value in [('title', post['title']), ('link', absolute(post['path'])), ('description', post['summary']), ('category', post['category']), ('guid', absolute(post['path'])), ('pubDate', format_datetime(datetime.combine(post['date_obj'], time(12), tzinfo=timezone.utc)))]:
            ET.SubElement(item, key).text = value
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(rss, encoding='unicode')


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    write('index.html', home())
    write('notes/index.html', notes())
    write('archive/index.html', archive())
    write('about/index.html', about())
    write('404.html', page('页面未找到', f'<main id="main" class="wrap not-found"><div class="eyebrow">PAGE NOT FOUND</div><h1>404</h1><p>这一页暂时没有文字。去其他地方看看吧。</p><a class="pill-link" href="{url()}">回到首页</a></main>', path='404.html'))
    for index, post in enumerate(POSTS):
        write(f'{post["path"]}index.html', article(post, index))
    write('feed.xml', feed())
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    sitemap = ET.Element(f'{{{ns}}}urlset')
    for path in ['', 'notes/', 'archive/', 'about/', *(post['path'] for post in POSTS)]:
        entry = ET.SubElement(sitemap, f'{{{ns}}}url')
        ET.SubElement(entry, f'{{{ns}}}loc').text = absolute(path)
    write('sitemap.xml', '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(sitemap, encoding='unicode'))
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {absolute("sitemap.xml")}\n')
    write('.nojekyll', '')
    print(f'Built {len(POSTS)} posts and 5 pages → {OUT}')


if __name__ == '__main__':
    build()
