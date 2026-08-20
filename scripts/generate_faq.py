import json
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, ".")

from app.config import settings

CHAT_MODEL = "llama3.1:latest"
OUTPUT_FILE = Path("data/seed/faq_docs.json")

SOURCES = {
    "terms": ("data/terms.md", "terms"),
    "about": ("data/about.md", "company"),
    "privacy": ("data/privacy.md", "privacy"),
}

PROMPT = """You are generating an FAQ dataset from the source document below.

Read the document and produce a JSON array of question/answer pairs that a customer
would realistically ask, answerable directly from this document.

Rules:
- Cover every distinct topic/section in the document, one or more Q&A pairs per section.
- Answers must be self-contained and accurate to the source. Do not invent facts not in the document.
- Questions must be phrased naturally, the way a real user would ask them.

Document:
{content}
"""


QA_SCHEMA = {
    "type": "object",
    "properties": {
        "faqs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                },
                "required": ["question", "answer"],
            },
        }
    },
    "required": ["faqs"],
}


def generate_qa(content: str) -> list[dict]:
    resp = httpx.post(
        f"{settings.OLLAMA_URL}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": PROMPT.format(content=content),
            "stream": False,
            "format": QA_SCHEMA,
        },
        timeout=180,
    )
    resp.raise_for_status()
    text = resp.json()["response"].strip()
    parsed = json.loads(text)
    return parsed["faqs"]


def main() -> None:
    all_docs = []
    for name, (path, category) in SOURCES.items():
        print(f"Generating FAQs from {path}")
        content = Path(path).read_text()
        qa_pairs = generate_qa(content)
        for pair in qa_pairs:
            all_docs.append(
                {
                    "category": category,
                    "question": pair["question"].strip(),
                    "answer": pair["answer"].strip(),
                }
            )
        print(f"  {len(qa_pairs)} pairs")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(all_docs, indent=2) + "\n")
    print(f"Wrote {len(all_docs)} total FAQ entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
