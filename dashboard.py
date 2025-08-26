import os, json, re, yaml
from pathlib import Path
import streamlit as st
from utils import load_config, est_reading_time, naive_keyword_density, seo_slug, read_structure, ensure_dir
import subprocess

BASE = Path(__file__).parent
cfg = load_config(BASE)
OUT = BASE / cfg["paths"]["output_dir"]
STRUCTURE_TEXT = read_structure(BASE, cfg["paths"]["structure_path"])

st.set_page_config(page_title="BlogGen Dashboard", layout="wide")

st.title("📚 BlogGen — Live Dashboard")

with st.sidebar:
    st.header("Defaults")
    d = cfg.get("defaults", {})
    author_name = st.text_input("Author Name", d.get("author_name", ""))
    author_title = st.text_input("Author Title", d.get("author_title", ""))
    audience = st.text_input("Audience", d.get("audience", ""))
    year = st.number_input("Year", value=int(d.get("year", 2025)))
    company_name = st.text_input("Company", d.get("company_name", "WIF Marketing"))
    primary_keyword_default = d.get("primary_keyword", "performance marketing")

st.subheader("Generate New Blog")
col1, col2 = st.columns([2,1])
with col1:
    topic = st.text_input("Topic", placeholder="e.g., The difference between 2x ROAS and 6x ROAS")
    primary_keyword = st.text_input("Primary Keyword", value=primary_keyword_default)
    use_ai = st.checkbox("Use AI (OpenRouter)", value=True)
with col2:
    st.caption("The generator follows your exact structure:")
    with st.expander("View Structure"):
        st.code(STRUCTURE_TEXT[:4000])

gen_clicked = st.button("Generate Blog")

if gen_clicked and topic and audience and author_name and author_title:
    # Call generator.py as a subprocess to keep logic single-sourced
    cmd = [
        "python", str(BASE / "generator.py"),
        "--topic", topic,
        "--audience", audience,
        "--primary_keyword", primary_keyword,
        "--author_name", author_name,
        "--author_title", author_title,
        "--company_name", company_name,
        "--year", str(year),
        "--use_ai", "true" if use_ai else "false"
    ]
    with st.spinner("Generating..."):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=120)
            st.success(out)
        except subprocess.CalledProcessError as e:
            st.error(e.output)
        except Exception as ex:
            st.error(str(ex))

st.divider()
st.subheader("Generated Posts")
ensure_dir(OUT)
files = sorted(list(OUT.glob("*.md")), key=lambda p: p.stat().st_mtime, reverse=True)

if not files:
    st.info("No posts yet. Generate your first blog above.")
else:
    for f in files:
        with st.expander(f.name):
            md = f.read_text(encoding="utf-8")
            # crude front-matter parse
            fm = {}
            if md.startswith("---"):
                try:
                    part = md.split("---", 2)
                    fm = yaml.safe_load(part[1]) or {}
                    body = part[2]
                except Exception:
                    body = md
            else:
                body = md

            title = fm.get("title", f.stem.replace("-", " ").title())
            st.markdown(f"### {title}")
            st.write(f"**Slug:** {fm.get('slug','')}  |  **Reading time:** {fm.get('reading_time_min','?')} min  |  **Date:** {fm.get('date','')}")
            st.code(body[:8000])

            with st.popover("SEO Checks"):
                kw = st.text_input(f"Primary keyword for {f.name}", value=fm.get("primary_keyword",""))
                dens = naive_keyword_density(body, kw) if kw else 0.0
                title_len = len(title)
                title_ok = cfg["seo"]["title_min"] <= title_len <= cfg["seo"]["title_max"]
                st.write(f"- Title length: {title_len} chars ({'OK' if title_ok else 'Adjust to 45–62'})")
                st.write(f"- Keyword density: {dens}% (aim ~0.5–2.0%)")
                st.write(f"- H2/H3 present: {'Yes' if ('## ' in body or '### ' in body) else 'No'}")
                st.write(f"- Reading time: {fm.get('reading_time_min','?')} min")

            # Inline edit
            edited = st.text_area("Edit Markdown", body, height=220, key=f"edit_{f.name}")
            if st.button("Save Changes", key=f"save_{f.name}"):
                if md.startswith("---"):
                    new_content = "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n" + edited
                else:
                    new_content = edited
                f.write_text(new_content, encoding="utf-8")
                st.success("Saved.")

            colA, colB = st.columns(2)
            with colA:
                if st.download_button("Download .md", data=md.encode("utf-8"), file_name=f.name, mime="text/markdown"):
                    st.toast("Downloaded")
            with colB:
                if st.button("Recompute Reading Time", key=f"rt_{f.name}"):
                    import re
                    words = len(re.findall(r"\w+", body))
                    mins = max(1, round(words/200))
                    fm["reading_time_min"] = int(mins)
                    new_content = "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n" + body
                    f.write_text(new_content, encoding="utf-8")
                    st.success("Updated reading time.")

st.caption("Tip: Set OPENROUTER_API_KEY in your environment for AI writes. Model: meta-llama/llama-3.3-8b-instruct:free")
