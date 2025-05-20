import fitz  # PyMuPD

def extract_urls_from_pdf(pdf_path):
    urls = set()
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        links = page.get_links()
        for link in links:
            uri = link.get("uri", None)
            if uri:
                urls.add(uri)
    # Chuyển set thành list các đối tượng có cấu trúc {url: string}
    return [{"url": url} for url in urls]