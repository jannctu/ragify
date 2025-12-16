"""
Synchronous PDF -> images -> OCR -> plain text knowledge.

No LLM, no vision model.
Suitable for scanned PDFs or low-quality text PDFs.
"""

import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from pdf2image import convert_from_path
import pytesseract

load_dotenv()


def safe_filename(name: str) -> str:
    name = os.path.splitext(name)[0]
    name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name).strip("_")
    return name or "document"


def normalize_text(text: str) -> str:
    """
    Cleanup OCR output for storage / embedding:
    - remove null chars
    - normalize spaces
    - collapse excessive newlines
    """
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def pdf_to_images(pdf_path: str, dpi: int = 250):
    """
    Convert PDF pages to PIL Images.
    Higher DPI = better OCR, slower.
    """
    return convert_from_path(pdf_path, dpi=dpi)


def ocr_image(image, lang: str = "eng") -> str:
    """
    OCR single image using Tesseract.
    """
    config = "--oem 3 --psm 6"  # balanced for document blocks
    text = pytesseract.image_to_string(
        image,
        lang=lang,
        config=config
    )
    return normalize_text(text)


def extract_knowledge_from_pdf_ocr(
    pdf_path: str,
    dpi: int = 250,
    lang: str = "eng",
) -> List[Dict]:
    """
    OCR-based pipeline:
      1. PDF -> images
      2. OCR each page
      3. Return list of {page, source, content}
    """
    images = pdf_to_images(pdf_path, dpi=dpi)
    results: List[Dict] = []

    total_pages = len(images)
    for idx, img in enumerate(images, start=1):
        print(f"[INFO] OCR processing page {idx}/{total_pages}...")
        text = ocr_image(img, lang=lang)

        results.append(
            {
                "page": idx,
                "source": os.path.basename(pdf_path),
                "content": text,
            }
        )

    return results


def save_outputs(pages: List[Dict], output_dir: str = "outputs") -> None:
    os.makedirs(output_dir, exist_ok=True)

    if not pages:
        print("[WARN] No pages extracted.")
        return

    doc_base = safe_filename(pages[0]["source"])

    # 1) Save per page
    for p in pages:
        page_num = int(p["page"])
        out_path = os.path.join(
            output_dir,
            f"{doc_base}_page_{page_num:03d}.txt"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            f.write((p["content"] or "").rstrip() + "\n")
        print(f"[OK] Saved: {out_path}")

    # 2) Save combined
    combined_path = os.path.join(
        output_dir,
        f"{doc_base}_ALL.txt"
    )
    with open(combined_path, "w", encoding="utf-8") as f:
        for p in pages:
            f.write(f"{pages[0]['source']} — Page {p['page']}\n\n")
            f.write((p["content"] or "").rstrip() + "\n\n")
            f.write("---\n\n")
    print(f"[OK] Saved combined: {combined_path}")


if __name__ == "__main__":
    pdf_file = "files/Indonesia-Salary-Guide-2025.pdf"

    pages = extract_knowledge_from_pdf_ocr(
        pdf_file,
        dpi=250,
        lang="eng"  # bisa "eng+ind"
    )

    save_outputs(pages, output_dir="outputs")

    print(
        f"\n[DONE] OCR extracted {len(pages)} pages from "
        f"{os.path.basename(pdf_file)}"
    )
