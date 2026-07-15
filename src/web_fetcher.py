"""web_fetcher.py — Lấy nội dung từ URL web cho Server"""

import requests
from bs4 import BeautifulSoup


def fetch_web_content(url: str) -> str:
    """
    Lấy nội dung chính từ URL web.
    Trả về text đã được làm sạch (bỏ nav, sidebar, footer, script, style).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()

        if resp.encoding and resp.encoding.lower() != "utf-8":
            resp.encoding = resp.apparent_encoding

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "noscript", "iframe", "form",
                         "button", "input", "select", "textarea"]):
            tag.decompose()

        article = soup.find("article") or soup.find("main") or soup.find("body")

        if article:
            text = article.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        cleaned = "\n".join(lines)

        MAX_CHARS = 15000
        if len(cleaned) > MAX_CHARS:
            cleaned = cleaned[:MAX_CHARS] + "\n\n[... nội dung bị cắt do quá dài ...]"

        return cleaned

    except requests.exceptions.Timeout:
        return "⚠️ Lỗi: Request timeout. Vui lòng kiểm tra URL hoặc kết nối mạng."
    except requests.exceptions.HTTPError as e:
        return f"⚠️ Lỗi HTTP: {e}"
    except requests.exceptions.RequestException as e:
        return f"⚠️ Lỗi kết nối: {e}"
    except Exception as e:
        return f"⚠️ Lỗi không xác định: {e}"
