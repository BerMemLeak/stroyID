"""PDF text assertions must ignore platform-specific whitespace from font encodings."""


def normalize_pdf_text(text):
    return ' '.join((text or '').split())


def page_text(page):
    return normalize_pdf_text(page.extract_text())
