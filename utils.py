import re, math, json, os, yaml, datetime
from pathlib import Path
from slugify import slugify
from jinja2 import Template
from markdown import markdown
from bs4 import BeautifulSoup

def load_config(base: Path) -> dict:
    fp = base / "config.yaml"
    return yaml.safe_load(fp.read_text(encoding="utf-8")) if fp.exists() else {}

def read_structure(base: Path, path: str) -> str:
    return (base / path).read_text(encoding="utf-8")

def seo_slug(title: str) -> str:
    return slugify(title)[:120]

def est_reading_time(text: str) -> int:
    words = len(re.findall(r"\w+", text))
    return max(1, math.ceil(words/200))

def naive_keyword_density(text: str, keyword: str) -> float:
    if not keyword:
        return 0.0
    text_low = text.lower()
    total_words = len(re.findall(r"\w+", text_low)) or 1
    hits = len(re.findall(re.escape(keyword.lower()), text_low))
    return round((hits/total_words)*100, 2)

def front_matter(meta: dict) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n"

def now_date_str() -> str:
    return datetime.date.today().isoformat()

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def md_to_html(md_text: str) -> str:
    html = markdown(md_text, extensions=["tables","fenced_code","toc","nl2br"])
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            a["target"] = "_blank"
            a["rel"] = "noopener noreferrer"
    return str(soup)

def build_jsonld(meta: dict, summary: str):
    schema = {
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": meta.get("title"),
      "description": summary,
      "author": {"@type": "Person", "name": meta.get("author", {}).get("name")},
      "publisher": {"@type": "Organization", "name": "WIF Marketing", "url": "https://wifmarketing.co"},
      "datePublished": meta.get("date"),
      "mainEntityOfPage": meta.get("canonical_url", "https://wifmarketing.co"),
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def render_html(template_str: str, meta: dict, md_body: str, internal_links: list):
    html_body = md_to_html(md_body)
    tpl = Template(template_str)
    jsonld = build_jsonld(meta, meta.get("meta_description",""))
    out = tpl.render(title=meta.get("title",""),
                     meta_description=meta.get("meta_description",""),
                     author_name=meta.get("author",{}).get("name",""),
                     keywords=", ".join(meta.get("keywords",[])),
                     canonical_url=meta.get("canonical_url",""),
                     og_title=meta.get("og_title", meta.get("title","")),
                     og_description=meta.get("og_description", meta.get("meta_description","")),
                     site_name=meta.get("company",""),
                     og_image=meta.get("og_image",""),
                     jsonld=jsonld,
                     date=meta.get("date",""),
                     reading_time=meta.get("reading_time_min",0),
                     content=html_body,
                     internal_links=internal_links)
    return out
