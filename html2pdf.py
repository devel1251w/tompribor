# html_to_pdf_sync.py
from playwright.sync_api import sync_playwright
from PyPDF2 import PdfMerger
from pathlib import Path


def html_to_pdf(input_html: str, output_pdf: str):
    """Конвертация HTML → PDF без asyncio, надёжно под Flask."""
    html_path = Path(input_html).resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--allow-file-access-from-files"
            ]
        )
        page = browser.new_page()
        page.goto(html_path, wait_until="networkidle")
        page.pdf(
            path=output_pdf,
            format="A4",
            scale=0.8,
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()
    print(f"✅ PDF создан: {output_pdf}")


def merge_pdfs(pdf_list, output_pdf):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_pdf)
    merger.close()
    print(f"📄 Итоговый PDF создан: {output_pdf}")


def process(in_html: str, out_pdf: str):
    """Полностью синхронный процесс."""
    input_html2 = "static/map.html"
    temp_pdf1 = "tmp/m.pdf"
    temp_pdf2 = "tmp/map.pdf"

    html_to_pdf(in_html, temp_pdf1)
    html_to_pdf(input_html2, temp_pdf2)
    merge_pdfs([temp_pdf1, temp_pdf2], out_pdf)
