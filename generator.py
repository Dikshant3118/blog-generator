import argparse, os, requests, json
from pathlib import Path
import yaml
import re
from utils import (
    load_config, read_structure, seo_slug, est_reading_time,
    front_matter, now_date_str, ensure_dir, render_html
)

BASE = Path(__file__).parent


def load_blog_parts(structure_path: Path):
    """Split the blog structure file into Part 1 and Part 2."""
    text = structure_path.read_text(encoding="utf-8")
    parts = text.split("Part 2:")
    part1 = parts[0].strip()
    part2 = "Part 2:" + parts[1].strip() if len(parts) > 1 else ""
    return part1, part2


def call_openai(part1: str, part2: str, topic: str, audience: str, api_key_env: str) -> str:
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key in environment: {api_key_env}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    messages = [
        {"role": "system", "content": "You are an expert content strategist and technical writer."},
        {"role": "system", "content": part1},
        {
            "role": "user",
            "content": part2 + f"\n\nTopic: {topic}\nAudience: {audience}\n"
        },
    ]

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json={
            "model": "gpt-4.1",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 8192,
        },
        timeout=180,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def clean_headings(md: str) -> str:
    # Remove "Module X:" prefixes but keep the rest
    return re.sub(r'(?im)^#+\s*Module\s+\d+:\s*', r'## ', md)


def render_blog(meta: dict, body: str) -> str:
    fm = front_matter(meta)
    return fm + "\n" + body.strip() + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--primary_keyword", required=True)
    parser.add_argument("--author_name", required=True)
    parser.add_argument("--author_title", required=True)
    parser.add_argument("--company_name", default="WIF Marketing")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--use_ai", type=str, default="true", help="true/false")
    args = parser.parse_args()

    cfg = load_config(BASE)
    structure_path = BASE / cfg["paths"]["structure_path"]
    part1, part2 = load_blog_parts(structure_path)
    use_ai = str(args.use_ai).lower() in ("true", "1", "yes", "y")

    if use_ai:
        body_md = call_openai(
            part1,
            part2,
            args.topic,
            args.audience,
            api_key_env="OPENAI_API_KEY"
        )
    else:
        body_md = f"> TODO: Write blog content for topic '{args.topic}'.\n\n---\n\n{part1}\n\n{part2}"

    meta = {
        "title": f"{args.topic} — Complete Guide for {args.year}",
        "author": {"name": args.author_name, "title": args.author_title},
        "date": now_date_str(),
        "primary_keyword": args.primary_keyword,
        "audience": args.audience,
        "company": args.company_name,
        "slug": "",
        "reading_time_min": 0,
        "keywords": [args.primary_keyword],
        "meta_description": "",
        "og_image": "",
        "og_title": "",
        "og_description": "",
        "canonical_url": ""
    }

    rt = est_reading_time(body_md)
    slug = seo_slug(meta["title"])
    meta["reading_time_min"] = rt
    meta["slug"] = slug
    meta["meta_description"] = body_md.strip()[:155]

    content_md = render_blog(meta, body_md)
    body_md = clean_headings(body_md)

    out_dir = BASE / cfg["paths"].get("output_dir", "output")
    ensure_dir(out_dir)
    md_path = out_dir / f"{slug}.md"
    md_path.write_text(content_md, encoding="utf-8")
    print(f"Generated Markdown: {md_path}")

    try:
        tpl = (BASE / "templates" / "html_template.html").read_text(encoding="utf-8")
        meta.setdefault("og_title", meta.get("title"))
        meta.setdefault("og_description", meta.get("meta_description"))
        meta.setdefault("canonical_url", f"https://yourdomain.com/{slug}.html")
        html_str = render_html(tpl, meta, body_md, internal_links=[])
        html_path = out_dir / f"{slug}.html"
        html_path.write_text(html_str, encoding="utf-8")
        print(f"Generated HTML: {html_path}")
        robots = out_dir / "robots.txt"
        if not robots.exists():
            robots.write_text(
                "User-agent: *\nAllow: /\nSitemap: https://wifmarketing.co/sitemap.xml\n",
                encoding="utf-8"
            )
    except Exception as e:  
        print("HTML export failed:", e)

if __name__ == "__main__":
    main()
