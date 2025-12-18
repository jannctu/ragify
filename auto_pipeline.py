"""
Auto-fallback PDF extraction pipeline.

Flow:
    1. Try native text extraction (pdfplumber)
    2. If quality is LOW -> OCR the page
    3. If OCR still LOW -> escalate to vision LLM
"""

import os
from typing import Dict, List

from pdf2image import convert_from_path

from vision_llm import call_llm_vision, image_to_base64_png
from pdf_to_ocr import ocr_image
from pdf_to_text_no_llm import extract_text_from_pdf, safe_filename
from quality_gate import evaluate_page_quality


def _load_page_image(pdf_path: str, page_number: int, dpi: int) -> object:
    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=page_number,
        last_page=page_number,
    )
    if not images:
        raise RuntimeError(f"Failed to render page {page_number}")
    return images[0]


def _record_attempt(report: Dict[str, object]) -> Dict[str, object]:
    return {
        "method": report["method"],
        "quality": report["quality"],
        "reason": report["reason"],
        "quality_metrics": report.get("metrics") or report.get("quality_metrics", {}),
    }


def extract_with_auto_fallback(
    pdf_path: str,
    ocr_dpi: int = 250,
    ocr_lang: str = "eng",
    vision_dpi: int = 200,
) -> List[Dict]:
    base_pages = extract_text_from_pdf(pdf_path)
    final_pages: List[Dict] = []

    for base in base_pages:
        page_num = base["page"]
        record = {
            "page": page_num,
            "source": base["source"],
            "content": base["content"],
            "method": base["method"],
            "quality": base["quality"],
            "reason": base["reason"],
            "quality_metrics": base["quality_metrics"],
            "attempts": [
                {
                    "method": base["method"],
                    "quality": base["quality"],
                    "reason": base["reason"],
                    "quality_metrics": base["quality_metrics"],
                }
            ],
        }

        if base["quality"] == "ok":
            final_pages.append(record)
            continue

        print(
            f"[WARN] Page {page_num}: text extraction quality LOW "
            f"({base['reason']}) -> running OCR"
        )
        page_image = _load_page_image(pdf_path, page_num, dpi=ocr_dpi)
        ocr_text = ocr_image(page_image, lang=ocr_lang)
        ocr_report = evaluate_page_quality(ocr_text, method="ocr")
        record["attempts"].append(_record_attempt({"method": "ocr", **ocr_report}))

        if ocr_report["quality"] == "ok":
            record.update(
                {
                    "content": ocr_text,
                    "method": "ocr",
                    "quality": ocr_report["quality"],
                    "reason": ocr_report["reason"],
                    "quality_metrics": ocr_report["metrics"],
                }
            )
            final_pages.append(record)
            continue

        print(
            f"[WARN] Page {page_num}: OCR quality still LOW "
            f"({ocr_report['reason']}) -> escalating to vision LLM"
        )
        if vision_dpi != ocr_dpi:
            page_image = _load_page_image(pdf_path, page_num, dpi=vision_dpi)

        b64_img = image_to_base64_png(page_image)
        rich_text = call_llm_vision(b64_img)
        vision_report = evaluate_page_quality(rich_text, method="vision")
        record["attempts"].append(
            _record_attempt({"method": "vision", **vision_report})
        )
        record.update(
            {
                "content": rich_text,
                "method": "vision",
                "quality": vision_report["quality"],
                "reason": vision_report["reason"],
                "quality_metrics": vision_report["metrics"],
            }
        )
        final_pages.append(record)

    return final_pages


def save_outputs(pages: List[Dict], output_dir: str = "outputs") -> None:
    os.makedirs(output_dir, exist_ok=True)

    if not pages:
        print("[WARN] No pages extracted.")
        return

    doc_base = safe_filename(pages[0]["source"])

    for p in pages:
        page_num = int(p["page"])
        out_path = os.path.join(output_dir, f"{doc_base}_page_{page_num:03d}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"> Method: {p['method']} | Quality: {p['quality']}\n\n")
            f.write((p["content"] or "").rstrip() + "\n")
        print(f"[OK] Saved: {out_path}")

    combined_path = os.path.join(output_dir, f"{doc_base}_ALL.md")
    with open(combined_path, "w", encoding="utf-8") as f:
        for p in pages:
            f.write(f"# {pages[0]['source']} — Page {p['page']}\n")
            f.write(f"_Method: {p['method']} · Quality: {p['quality']}_\n\n")
            f.write((p["content"] or "").rstrip() + "\n\n")
            f.write("---\n\n")
    print(f"[OK] Saved combined: {combined_path}")


if __name__ == "__main__":
    pdf_file = "files/Indonesia-Salary-Guide-2025.pdf"
    pages = extract_with_auto_fallback(pdf_file)
    save_outputs(pages, output_dir="outputs")
    print(
        f"\n[DONE] Auto pipeline finished {len(pages)} pages from "
        f"{os.path.basename(pdf_file)}"
    )
