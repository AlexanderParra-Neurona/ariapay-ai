import sys
from pathlib import Path

import httpx
import trafilatura

sys.path.insert(0, ".")

from app.config import settings

OUTPUT_DIR = Path("data")
CHAT_MODEL = "llama3.1:latest"

PAGES = {
    "terms": "https://www.ariapay.id/apps/en/terms",
    "about": "https://www.ariapay.id/apps/en/about",
    "privacy": "https://www.ariapay.id/apps/en/privacy",
}

PROMPT = """Convert the following webpage content into clean, well-structured Markdown.

Rules:
- Preserve all headings, lists, and paragraph structure.
- Do not add commentary, preambles, or explanations.
- Do not invent content that isn't present in the source.
- Output only the Markdown, nothing else.

Content:
{content}
"""


def fetch_html(url: str) -> str:
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def extract_main_content(html: str) -> str:
    extracted = trafilatura.extract(html, output_format="markdown", include_links=True)
    if not extracted:
        raise ValueError("trafilatura extracted no content")
    return extracted


def markdownify_with_llm(content: str) -> str:
    resp = httpx.post(
        f"{settings.OLLAMA_URL}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": PROMPT.format(content=content),
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    markdown = resp.json()["response"].strip()
    if markdown.startswith("```"):
        markdown = markdown.split("\n", 1)[1]
        markdown = markdown.rsplit("```", 1)[0].strip()
    return markdown


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in PAGES.items():
        print(f"Fetching {url}")
        html = fetch_html(url)
        extracted = extract_main_content(html)
        markdown = markdownify_with_llm(extracted)
        out_path = OUTPUT_DIR / f"{name}.md"
        out_path.write_text(markdown)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
