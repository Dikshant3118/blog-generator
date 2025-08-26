import argparse, csv, os, yaml, json
from pathlib import Path
from generator import build_prompt, call_openrouter, render_blog, now_date_str
from utils import load_config, read_structure, seo_slug, est_reading_time, front_matter, ensure_dir, md_to_html, render_html, suggest_internal_links
BASE = Path(__file__).parent

def generate_one(row, cfg, structure_text, use_ai=True):
    topic = row.get("topic") or row.get("title") or ""
    audience = row.get("audience") or cfg.get("defaults",{}).get("audience","")
    pk = row.get("primary_keyword") or cfg.get("defaults",{}).get("primary_keyword","")
    author_name = row.get("author_name") or cfg.get("defaults",{}).get("author_name","WIF Marketing")
    author_title = row.get("author_title") or cfg.get("defaults",{}).get("author_title","")
    company = row.get("company") or cfg.get("defaults",{}).get("company_name","WIF Marketing")
    year = int(row.get("year") or cfg.get("defaults",{}).get("year",2025))
    sys_prompt = "You are an expert content strategist and technical writer. Follow the provided structure precisely, keep tone authoritative yet accessible, and bias towards actionable specificity."
    if use_ai:
        prompt = build_prompt(structure_text, topic, audience, year, author_name, author_title, pk, company)
        body_md = call_openrouter(prompt, sys_prompt, cfg["model"]["name"], cfg["model"]["api_base"], cfg["model"]["key_env"])
    else:
        body_md = f"## Draft: {topic}\\n\\n(Please fill this)\\n\\n{structure_text}"
    meta = {
        "title": row.get("title") or f"{topic} — A Complete Guide",
        "author": {"name": author_name, "title": author_title},
        "date": now_date_str(),
        "primary_keyword": pk,
        "audience": audience,
        "company": company,
        "slug": seo_slug(topic),
        "reading_time_min": 0,
        "canonical_url": row.get("canonical_url",""),
        "keywords": [pk] + [k.strip() for k in (row.get("keywords","") or "").split(",") if k.strip()],
        "meta_description": row.get("meta_description",""),
        "og_image": row.get("og_image",""),
        "og_title": row.get("og_title",""),
        "og_description": row.get("og_description",""),
    }
    # compute reading time
    rt = est_reading_time(body_md)
    meta["reading_time_min"] = rt
    # save markdown
    out_dir = BASE / "output"
    ensure_dir(out_dir)
    md_path = out_dir / (meta["slug"] + ".md")
    content = front_matter(meta) + "\n" + body_md
    md_path.write_text(content, encoding="utf-8")
    return {"meta": meta, "body": body_md, "md_path": str(md_path)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--use_ai", default="true")
    args = parser.parse_args()
    cfg = load_config(BASE)
    structure_text = read_structure(BASE, cfg["paths"]["structure_path"])
    rows = []
    with open(args.csv, newline='', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append(r)
    results = []
    for r in rows:
        res = generate_one(r, cfg, structure_text, use_ai=str(args.use_ai).lower() in ("true","1","y","yes"))
        results.append(res)
    # Create internal link suggestions
    posts_meta = [{"title": r["meta"]["title"], "slug": r["meta"]["slug"], "canonical_url": r["meta"].get("canonical_url",""), "content": r["body"]} for r in results]
    link_suggestions = suggest_internal_links(posts_meta, top_n=4)
    # Render HTMLs with internal links
    tpl = Path(BASE / "templates" / "html_template.html").read_text(encoding="utf-8")
    for i, r in enumerate(results):
        internal_links = link_suggestions[i] if i < len(link_suggestions) else []
        html = render_html(tpl, r["meta"], r["body"], internal_links)
        html_path = Path(r["md_path"]).with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
    print(f"Generated {len(results)} posts in output/ (both .md and .html)")

if __name__ == '__main__':
    main()
