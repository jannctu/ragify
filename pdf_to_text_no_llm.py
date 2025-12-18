import os
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
import pdfplumber
from quality_gate import evaluate_page_quality

load_dotenv()


def safe_filename(name: str) -> str:
    name = os.path.splitext(name)[0]
    name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name).strip("_")
    return name or "document"


def normalize_text(text: str) -> str:
    """
    Basic cleanup biar lebih rapih untuk vector DB:
    - rapihin whitespace
    - collapse banyak newline berurutan
    """
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    PDF -> plain text per halaman (tanpa OCR).
    """
    results: List[Dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for idx, page in enumerate(pdf.pages, start=1):
            print(f"[INFO] Extracting text page {idx}/{total_pages}...")
            txt = page.extract_text() or ""
            txt = normalize_text(txt)

            quality_report = evaluate_page_quality(txt, method="text")

            results.append(
                {
                    "page": idx,
                    "source": os.path.basename(pdf_path),
                    "method": "text",
                    "quality": quality_report["quality"],
                    "reason": quality_report["reason"],
                    "quality_metrics": quality_report["metrics"],
                    "content": txt,
                }
            )
    return results


def save_outputs(pages: List[Dict], output_dir: str = "outputs") -> None:
    os.makedirs(output_dir, exist_ok=True)
    if not pages:
        print("[WARN] No pages extracted.")
        return

    doc_base = safe_filename(pages[0]["source"])

    # 1) per page
    for p in pages:
        page_num = int(p["page"])
        out_path = os.path.join(output_dir, f"{doc_base}_page_{page_num:03d}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write((p["content"] or "").rstrip() + "\n")
        print(f"[OK] Saved: {out_path}")

    # 2) combined
    combined_path = os.path.join(output_dir, f"{doc_base}_ALL.txt")
    with open(combined_path, "w", encoding="utf-8") as f:
        for p in pages:
            f.write(f"{pages[0]['source']} — Page {p['page']}\n")
            f.write((p["content"] or "").rstrip() + "\n")
            f.write("\n" + ("-" * 60) + "\n\n")
    print(f"[OK] Saved combined: {combined_path}")


if __name__ == "__main__":
    pdf_file = "files/Indonesia-Salary-Guide-2025.pdf"
    pages = extract_text_from_pdf(pdf_file)
    save_outputs(pages, output_dir="outputs")
    print(f"\n[DONE] Extracted {len(pages)} pages from {os.path.basename(pdf_file)}")
