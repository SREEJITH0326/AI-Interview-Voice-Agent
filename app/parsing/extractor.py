from pathlib import Path

import pdfplumber
from docx import Document


def extract_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        with pdfplumber.open(p) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif suffix == ".docx":
        text = "\n".join(par.text for par in Document(p).paragraphs)
    elif suffix in {".txt", ".md"}:
        text = p.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    text = text.strip()
    if not text:
        raise ValueError(f"No text extracted from {path} (scanned PDF? needs OCR)")
    return text