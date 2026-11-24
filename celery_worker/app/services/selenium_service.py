import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin

SUPPORTED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"]

# --- Cấu hình Selenium ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--headless=new")
options.add_argument('--no-sandbox')
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

def crawl_urls_with_selenium(url, wait_time=5):
    """
    Hàm này dùng Selenium để lấy tất cả URL ảnh và PDF từ một trang web,
    kể cả các nội dung được tải động bằng JavaScript.
    """
    # # --- Cấu hình Selenium ---
    # options = Options()
    # # Chạy ở chế độ "headless" (không mở cửa sổ trình duyệt)
    # # Bỏ dòng này nếu bạn muốn thấy trình duyệt hoạt động
    # options.add_argument('--headless') 
    # options.add_argument('--log-level=3') # Giảm bớt log không cần thiết trên console
    # options.add_argument('--disable-gpu')
    # options.add_argument('--window-size=1920,1080')

    # # Tự động cài đặt và cấu hình chromedriver
    # service = ChromeService(ChromeDriverManager().install())
    
    # # Khởi tạo trình duyệt
    # driver = webdriver.Chrome(service=service, options=options)

    # Dùng set để lưu các URL, tránh bị trùng lặp
    image_urls = set()
    pdf_urls = set()

    try:
        # Mở URL
        print(f"Đang truy cập trang: {url}...")
        driver.get(url)

        # --- Chờ để nội dung động tải xong ---
        # Đây là cách đơn giản nhất: chờ một khoảng thời gian cố định.
        print(f"Chờ {wait_time} giây để nội dung động (JavaScript) tải xong...")
        time.sleep(wait_time)
        
        # Có thể thêm hành động cuộn trang để kích hoạt lazy loading
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(2) # Chờ thêm sau khi cuộn

        # Lấy mã nguồn của trang sau khi JavaScript đã chạy
        page_source = driver.page_source

        # Phân tích HTML bằng Beautiful Soup
        soup = BeautifulSoup(page_source, 'lxml')

        # --- 1. Lấy URL hình ảnh ---
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src')
            if src:
                if any(src.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    full_url = urljoin(url, src)
                    image_urls.add(full_url)

        # --- 2. Lấy URL file PDF ---
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.lower().endswith('.pdf'):
                full_url = urljoin(url, href)
                pdf_urls.add(full_url)
        
        return list(image_urls), list(pdf_urls)

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return [], []
    finally:
        # Luôn đóng trình duyệt sau khi hoàn thành, kể cả khi có lỗi
        print("Đã hoàn thành. Đóng trình duyệt...")
        driver.quit()