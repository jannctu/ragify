"""
Simple synchronous PDF → images → LLM → rich text (markdown) pipeline.

Dependencies:
    pip install pdf2image pillow openai
OS:
    - Butuh poppler (Linux/Mac via package manager; Windows download poppler)
Env:
    - OPENAI_API_KEY harus sudah di-set
"""

import io   
import os
import base64
from typing import List, Dict
from dotenv import load_dotenv
import re
load_dotenv()  # otomatis load .env ke environment variables


from pdf2image import convert_from_path
from openai import OpenAI

client = OpenAI()


def pdf_to_images(pdf_path: str, dpi: int = 200):
    """
    Convert setiap halaman PDF → PIL.Image.
    Synchronous, jalan satu-satu.
    """
    return convert_from_path(pdf_path, dpi=dpi)


def image_to_base64_png(image) -> str:
    """
    Convert PIL.Image → base64 string (PNG).
    """
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


def call_llm_vision(image_b64: str) -> str:
    """
    Kirim 1 halaman (image base64) ke LLM vision
    dan terima 'rich text knowledge' siap masuk vector DB.
    """
    user_instructions = (
        "You will receive a screenshot of a single PDF page.\n"
        "Extract all useful information and rewrite it as **clean, well-structured markdown**:\n"
        "- Use headings, subheadings, bullet points, and numbered lists where helpful.\n"
        "- Fix obvious typos, but keep the original meaning.\n"
        "- Do NOT invent new content; only reorganize what's on the page.\n"
        "The output will be stored in a vector database, so keep it dense, self-contained, "
        "and suitable for retrieval."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # model vision yang ringan, synchronous OK
        messages=[
            {
                "role": "system",
                "content": "You are a precise knowledge extractor for PDF documents."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_instructions},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        },
                    },
                ],
            },
        ],
        temperature=0.1,
        max_tokens=1500,
    )

    return resp.choices[0].message.content.strip()


def extract_knowledge_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Pipeline synchronous:
      1. Baca PDF
      2. Screenshot tiap halaman
      3. Kirim ke LLM vision (sequential)
      4. Return list dict siap untuk di-upsert ke vector database

    Return format (contoh):
      [
        {
          "page": 1,
          "source": "mydoc.pdf",
          "content": "<markdown rich text>",
        },
        ...
      ]
    """
    images = pdf_to_images(pdf_path)
    results: List[Dict] = []

    total_pages = len(images)
    for idx, img in enumerate(images, start=1):
        print(f"[INFO] Processing page {idx}/{total_pages}...")
        b64_img = image_to_base64_png(img)
        rich_text = call_llm_vision(b64_img)

        results.append(
            {
                "page": idx,
                "source": os.path.basename(pdf_path),
                "content": rich_text,
            }
        )

    return results

def safe_filename(name: str) -> str:
    # buang karakter aneh biar aman di filesystem
    name = os.path.splitext(name)[0]
    name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name).strip("_")
    return name or "document"


def save_outputs(pages: List[Dict], output_dir: str = "outputs") -> None:
    os.makedirs(output_dir, exist_ok=True)

    if not pages:
        print("[WARN] No pages extracted.")
        return

    doc_base = safe_filename(pages[0]["source"])

    # 1) Save per page
    for p in pages:
        page_num = int(p["page"])
        out_path = os.path.join(output_dir, f"{doc_base}_page_{page_num:03d}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(p["content"].rstrip() + "\n")
        print(f"[OK] Saved: {out_path}")

    # 2) Save combined
    combined_path = os.path.join(output_dir, f"{doc_base}_ALL.md")
    with open(combined_path, "w", encoding="utf-8") as f:
        for p in pages:
            f.write(f"# {pages[0]['source']} — Page {p['page']}\n\n")
            f.write(p["content"].rstrip() + "\n\n---\n\n")
    print(f"[OK] Saved combined: {combined_path}")

if __name__ == "__main__":
    pdf_file = "files/Indonesia-Salary-Guide-2025.pdf"
    pages = extract_knowledge_from_pdf(pdf_file)

    # save ke folder outputs/
    save_outputs(pages, output_dir="outputs")

    # optional: print ringkas aja biar console ga banjir
    print(f"\n[DONE] Extracted {len(pages)} pages from {os.path.basename(pdf_file)}")
