import os
import re
import urllib3
from typing import Optional, Tuple, List
from langchain_community.document_loaders import WebBaseLoader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from urllib.parse import urlparse
from reportlab.lib.colors import blue

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thiết lập User-Agent
os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

# Đường dẫn thư mục lưu PDF
PDF_SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.makedirs(PDF_SAVE_DIR, exist_ok=True)


def slugify(value: str) -> str:
    """Chuyển tiêu đề thành định dạng an toàn cho tên file."""
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[\s_-]+', '-', value)


def clean_text(text: str) -> str:
    """Làm sạch nội dung HTML hoặc văn bản thô."""
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r"^[•\-]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[•\-]", "", text) 
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return '\n'.join(line.strip() for line in text.strip().splitlines())


def wrap_text(text: str, max_width: int, font_name: str, font_size: int) -> list:
    """Tách văn bản thành các dòng phù hợp với chiều rộng trang PDF."""
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split()
        current_line = ''
        for word in words:
            test_line = f"{current_line} {word}".strip()
            width = stringWidth(test_line, font_name, font_size)
            if width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        lines.append('')  
    return lines


def extract_text_and_title(url: str) -> Tuple[str, str]:
    """Lấy tiêu đề và nội dung chính từ trang web theo trình tự đúng."""
    try:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time
            
            # Cấu hình Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={os.environ['USER_AGENT']}")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.get(url)
            
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            last_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(0, last_height, 300):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.1)
            
            time.sleep(4)  
            
            title = driver.title
            
            driver.execute_script("""
                var elements = document.querySelectorAll('script, style, noscript, iframe');
                for (var i = 0; i < elements.length; i++) {
                    elements[i].remove();
                }
            """)
            
            main_content = None
            possible_containers = [
                "//article", "//main", "//*[@id='content']", "//*[@class='content']", 
                "//div[contains(@class,'article')]", "//div[contains(@class,'post')]",
                "//section[contains(@class,'main')]", "//div[contains(@class,'main')]"
            ]
            
            for selector in possible_containers:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    main_content = max(elements, key=lambda e: len(e.text.strip()))
                    break
            
            if not main_content or len(main_content.text) < 100:
                main_content = driver.find_element(By.TAG_NAME, "body")
            
            html_content = main_content.get_attribute('outerHTML')
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'svg']):
                tag.decompose()
            
            for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                header.insert_before('\n\n')
                header.insert_after('\n')
            
            for p in soup.find_all('p'):
                p.insert_after('\n')
            
            for li in soup.find_all('li'):
                li.insert_before('• ')
                li.insert_after('\n')
            
            content = soup.get_text(separator=' ')
            
            import re
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'\n\s*\n', '\n\n', content)
            
            lines = content.split('\n')
            unique_lines = []
            seen = set()
            
            for line in lines:
                line = line.strip()
                if line and line not in seen:
                    unique_lines.append(line)
                    seen.add(line)
            
            content = '\n'.join(unique_lines)
            
            driver.quit()
            return title, content
            
        except ImportError as e:
            print(f"[⚠️] Không thể sử dụng Selenium: {e}, sử dụng WebBaseLoader thay thế")
    
    except Exception as e:
        print(f"[❌] Lỗi khi trích xuất từ {url}: {e}")
        import traceback
        traceback.print_exc()
        return "no_title", ""


def save_text_to_pdf(text: str, path: str, title: str = "", url: str = "") -> bool:
    """Lưu văn bản vào PDF."""
    try:
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        margin = 50
        usable_width = width - 2 * margin

        title_font = "Helvetica-Bold"
        body_font = "Helvetica"
        url_font = "Helvetica-Oblique"
        title_size = 16
        body_size = 12
        url_size = 12
        line_height = body_size + 4

        y = height - margin

        if title:
            c.setFont(title_font, title_size)
            for line in wrap_text(title, usable_width, title_font, title_size):
                c.drawString(margin, y, line)
                y -= title_size + 6
            y -= 10

        c.setFont(body_font, body_size)
        for line in wrap_text(clean_text(text), usable_width, body_font, body_size):
            if y < margin:
                c.showPage()
                c.setFont(body_font, body_size)
                y = height - margin
            c.drawString(margin, y, ''.join(c if ord(c) < 128 else ' ' for c in line))
            y -= line_height


        if url:
            c.setFont(url_font, url_size)
            c.setFillColor(blue)  
            url_text = f"Link URL: {url}"
            
            url_width = stringWidth(url_text, url_font, url_size)
            x_position = (width - url_width) / 2
            
            c.linkURL(url, (x_position, margin - 20, x_position + url_width, margin - 10 + url_size), 
                     relative=1)
            c.drawString(x_position, margin - 20, url_text)

        c.save()
        print(f"[✅] Đã lưu PDF: {path}")
        return True
    except Exception as e:
        print(f"[❌] Không thể lưu PDF: {e}")
        return False


def save_url_to_pdf(url: str) -> Optional[str]:
    """Trích xuất và lưu trang web thành file PDF duy nhất."""
    title, content = extract_text_and_title(url)
    if not content:
        print(f"[⚠️] Không có nội dung từ: {url}")
        return None

    domain = urlparse(url).netloc
    pdf_name = f"{slugify(domain)}_{slugify(title)}.pdf"
    pdf_path = os.path.join(PDF_SAVE_DIR, pdf_name)

    if os.path.exists(pdf_path):
        print(f"[✅] PDF đã tồn tại: {pdf_path}")
        return pdf_path

    return pdf_path if save_text_to_pdf(content, pdf_path, title, url) else None

def read_urls_from_file(file_path: str) -> List[str]:
    """
    Đọc danh sách URL từ file text
    Args:
        file_path: Đường dẫn đến file chứa URLs
    Returns:
        List[str]: Danh sách các URL hợp lệ
    """
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if re.match(r'^https?://', line):
                        urls.append(line)
                    else:
                        print(f"[⚠️] URL không hợp lệ: {line}")
        return urls
    except Exception as e:
        print(f"[❌] Lỗi khi đọc file {file_path}: {e}")
        return []

def read_urls_from_file(filepath: str) -> List[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls

if __name__ == "__main__":
    # Load toàn bộ link crawl
    urls = read_urls_from_file('./data_source/generative_ai/url_list.txt')

    # load và lưu dữ liệu vào thư mục pdfs
    for url in urls:
        save_url_to_pdf(url)
