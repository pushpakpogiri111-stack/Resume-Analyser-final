from pdfminer.high_level import extract_text
import os


def _extract_with_pypdf(pdf_path):
    try:
        from PyPDF2 import PdfReader
    except ImportError as e:
        print(f"PyPDF2 is not installed: {e}")
        return ""

    try:
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        return "\n".join(pages).strip()
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
        return ""


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        text = extract_text(pdf_path)
        if text and text.strip():
            return text.strip()
    except Exception as e:
        print(f"pdfminer extraction failed: {e}")

    fallback_text = _extract_with_pypdf(pdf_path)
    return fallback_text.strip()
