#!/usr/bin/env python3
"""
Static site generator. Stdlib only — run `python3 build.py`.

Source layout:
  site.toml                 site config
  templates/page.html       shell for every page
  content/posts/*.html      one file per post (front matter + html body)

Generated into the repo root, because that is what GitHub Pages serves:
  index.html  posts/<slug>/index.html  404.html  index.xml  sitemap.xml  style.css
"""

import html
import os
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from email.utils import formatdate

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "site.toml")
TEMPLATES = os.path.join(ROOT, "templates")
POSTS_SRC = os.path.join(ROOT, "content", "posts")
TIMEZONE = timezone(timedelta(hours=0))

# Everything the previous Hugo build left behind. The generator owns the root;
# anything not regenerated is stale. Kept assets are re-written every build.
PRUNE_DIRS = ["css", "fonts", "categories", "tags", "page", "posts/page"]
PRUNE_FILES = [
    "bundle.min.js",
    "terminal.css",
    "og-image.png",
    "posts/index.html",
    "posts/index.xml",
    "index.xml",
    "sitemap.xml",
    "404.html",
    "index.html",
    "style.css",
]


# ---------------------------------------------------------------- config

def read_config():
    """Flat key = value config. Only what we actually need."""
    config = {"title": "", "description": "", "author": "", "base_url": "", "year": ""}
    if not os.path.exists(CONFIG_PATH):
        return config
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def read_template(name):
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
        return fh.read()


def render(template, values):
    """Token replacement. No str.format — CSS braces would eat us alive."""
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    return out


# ---------------------------------------------------------------- posts

POST_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<slug>[a-z0-9][a-z0-9-]*)\.html$")


def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    match = re.match(r"\A---\s*\n(.*?\n)---\s*\n", raw, re.S)
    meta = {}
    body = raw
    if match:
        body = raw[match.end():]
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()

    slug = POST_FILE.match(os.path.basename(path))
    if not slug:
        raise SystemExit(f"Post filename must be YYYY-MM-DD-slug.html, got {path}")

    try:
        posted = datetime.strptime(meta["date"], "%Y-%m-%d").replace(tzinfo=TIMEZONE)
    except (KeyError, ValueError) as err:
        raise SystemExit(f"{path}: bad or missing `date: YYYY-MM-DD` ({err})")

    return {
        "slug": slug.group("slug"),
        "title": meta.get("title", slug.group("slug")),
        "date": posted,
        "summary": meta.get("summary", ""),
        "body": body.strip(),
    }


def load_posts():
    if not os.path.isdir(POSTS_SRC):
        return []
    posts = [
        parse_post(os.path.join(POSTS_SRC, name))
        for name in sorted(os.listdir(POSTS_SRC))
        if name.endswith(".html")
    ]
    posts.sort(key=lambda p: p["date"], reverse=True)
    seen = {}
    for post in posts:
        if post["slug"] in seen:
            raise SystemExit(f"Duplicate slug: {post['slug']}")
        seen[post["slug"]] = True
    return posts


def excerpt(post, limit=280):
    """Strip tags for the listing blurb. Deliberately dumb."""
    text = re.sub(r"<[^>]+>", " ", post["body"])
    text = re.sub(r"\s+", " ", text).strip()
    if post["summary"]:
        return post["summary"]
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


# ---------------------------------------------------------------- writing

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content if content.endswith("\n") else content + "\n")
    print(f"  wrote {os.path.relpath(full, ROOT)}")


def prune():
    for name in PRUNE_DIRS:
        target = os.path.join(ROOT, name)
        if os.path.isdir(target):
            shutil.rmtree(target)
            print(f"  pruned {name}/")
    for name in PRUNE_FILES:
        target = os.path.join(ROOT, name)
        if os.path.isfile(target):
            os.remove(target)
            print(f"  pruned {name}")


def prune_stale_posts(posts):
    """Delete generated post dirs whose source file is gone. Without this a
deprecated post keeps serving at its old URL — out of the listing, the feed and
the sitemap, but still readable and still indexed."""
    if not os.path.isdir(POSTS_SRC):
        return  # nothing to compare against; don't wipe posts on a config slip
    live = {post["slug"] for post in posts}
    out = os.path.join(ROOT, "posts")
    if not os.path.isdir(out):
        return
    for name in sorted(os.listdir(out)):
        target = os.path.join(out, name)
        if os.path.isdir(target) and name not in live:
            shutil.rmtree(target)
            print(f"  pruned posts/{name}/ (no source post)")


def rfcdate(moment):
    return formatdate(moment.timestamp(), usegmt=True)


def iso(moment):
    return moment.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- pages

def page_shell(config, template, *, title, description, body):
    site = config["title"]
    full_title = site if title in ("", site) else (f"{title} · {site}" if site else title)
    return render(
        template,
        {
            "title": html.escape(full_title),
            "description": html.escape(description or config["description"]),
            "content": body,
            "author": html.escape(config["author"]),
            "year": str(config["year"] or date.today().year),
        },
    )


def index_body(posts, config):
    if not posts:
        return '  <p class="empty">Nothing here yet.</p>\n'
    out = ""
    for post in posts:
        out += f"""    <article>
      <h2 class="post-title"><a href="/posts/{post['slug']}/">{html.escape(post['title'])}</a></h2>
      <time class="post-date" datetime="{iso(post['date'])}">{iso(post['date'])}</time>
      <p class="post-excerpt">{html.escape(excerpt(post))}</p>
    </article>
"""
    return out


def post_body(post):
    return f"""  <article>
    <header class="post-header">
      <h1 class="post-title">{html.escape(post['title'])}</h1>
      <time class="post-date" datetime="{iso(post['date'])}">{iso(post['date'])}</time>
    </header>
{post['body']}
  </article>
"""


def not_found_body():
    return '  <h1 class="post-title">404</h1>\n  <p>That page does not exist. <a href="/">Back home</a>.</p>\n'


def rss(posts, config):
    base = config["base_url"].rstrip("/")
    updated = rfcdate(posts[0]["date"]) if posts else rfcdate(datetime.now(TIMEZONE))
    items = ""
    for post in posts:
        link = f"{base}/posts/{post['slug']}/"
        items += f"""    <item>
      <title>{html.escape(post['title'])}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <pubDate>{rfcdate(post['date'])}</pubDate>
      <description>{html.escape(excerpt(post))}</description>
    </item>
"""
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html.escape(config['title'])}</title>
    <link>{base}/</link>
    <description>{html.escape(config['description'])}</description>
    <generator>build.py</generator>
    <lastBuildDate>{updated}</lastBuildDate>
{items}  </channel>
</rss>
"""


def sitemap(posts, config):
    base = config["base_url"].rstrip("/")
    urls = [("index.html", f"{base}/")]
    urls += [(f"posts/{p['slug']}/index.html", f"{base}/posts/{p['slug']}/") for p in posts]
    out = ['<?xml version="1.0" encoding="utf-8" standalone="yes"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, loc in urls:
        stamp = iso(posts[0]["date"]) if posts else iso(date.today())
        out.append(f"  <url><loc>{loc}</loc><lastmod>{stamp}</lastmod></url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- main

def main():
    config = read_config()
    posts = load_posts()

    prune()
    prune_stale_posts(posts)

    write("style.css", read_template("style.css"))
    for asset in ("favicon.png", "apple-touch-icon.png"):
        source = os.path.join(ROOT, asset)
        if os.path.exists(source):
            print(f"  kept  {asset}")

    template = read_template("page.html")

    index = page_shell(
        config,
        template,
        title=config["title"],
        description=config["description"],
        body=index_body(posts, config),
    )
    write("index.html", index)

    for post in posts:
        write(
            f"posts/{post['slug']}/index.html",
            page_shell(
                config,
                template,
                title=post["title"],
                description=excerpt(post),
                body=post_body(post),
            ),
        )

    write(
        "404.html",
        page_shell(
            config,
            template,
            title="404",
            description="Page not found",
            body=not_found_body(),
        ),
    )
    write("index.xml", rss(posts, config))
    write("sitemap.xml", sitemap(posts, config))
    print(f"\n{len(posts)} post(s). Serve with: python3 -m http.server -d . 8000")


if __name__ == "__main__":
    main()
