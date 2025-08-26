# BlogGen + Live Dashboard (Python)

A practical, production-ready blog generator that follows your provided blog structure and a Streamlit-powered live dashboard to manage content generation, editing, and SEO checks.

## Features
- Generate long-form blogs in your exact structure (pulled from `templates/blog_structure.txt`).
- Optional AI drafting via OpenRouter (Llama 3.3 8B Instruct).
- Deterministic rendering using Jinja2 and Markdown.
- SEO checks (title length, headings, keyword coverage, reading time, internal links).
- Live dashboard to trigger generations, preview results, edit inline, and export.
- File-based outputs in `output/` with SEO-friendly slugs.

## Quick Start

1) **Install dependencies** (Python 3.10+ recommended):
```bash
pip install -r requirements.txt
```

2) **Set your OpenRouter key** (optional, only if you want AI autowriting):
```bash
# Windows (Powershell)
$Env:OPENROUTER_API_KEY="YOUR_KEY"

# macOS/Linux
export OPENROUTER_API_KEY="YOUR_KEY"
```
> Replace `YOUR_KEY` with your key. You mentioned one in chat; use that value directly if you choose.

3) **Generate a blog (CLI)**:
```bash
python generator.py \
  --topic "B2B Paid Ads" \
  --audience "B2B founders and performance marketers" \
  --primary_keyword "B2B paid ads" \
  --author_name "WIF Marketing" \
  --author_title "Performance Marketing Agency" \
  --year 2025 \
  --use_ai true
```

4) **Run the live dashboard**:
```bash
streamlit run dashboard.py
```

## Notes
- All generated markdown files land in `output/` with a front-matter block you can use in static site generators (Next.js, Hugo, Jekyll).
- The dashboard lets you regenerate sections with AI or keep them manual.
- The OpenRouter call is a single, simple endpoint: `POST https://openrouter.ai/api/v1/chat/completions`.


## Bulk generation from CSV

Create a CSV with header columns like: topic,title,primary_keyword,author_name,author_title,keywords,meta_description,og_image,canonical_url

Then run:

```
python bulk_generator.py --csv topics.csv --use_ai true
```

This will produce both `.md` and `.html` files in `output/`, and will compute internal link suggestions between generated posts.
