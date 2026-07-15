"""script_editor.py — Gọi LLM để biên tập audio script cho Server"""

import os
from pathlib import Path
from openai import OpenAI
from src.config_manager import ConfigManager


SYSTEM_PROMPT = (
    "Bạn là một chuyên gia Instructional Designer và Podcast Scriptwriter. "
    "Bạn có kỹ năng biến những tài liệu kỹ thuật (Technical Documentation) "
    "khô khan, phức tạp thành kịch bản nói (Audio Script) mượt mà, dễ tiếp thu "
    "nhưng vẫn đảm bảo tính chính xác tuyệt đối về kiến thức.\n\n"
    "Core Skills:\n"
    "- Audio-First Writing: Viết để nghe, không phải để đọc. Ưu tiên câu vừa đủ, nhịp điệu tự nhiên.\n"
    "- TTS Optimization: Am hiểu cách hoạt động của bộ đọc nhân tạo (TTS) để xử lý các ký hiệu, "
    "số thứ tự và từ viết tắt.\n"
    "- Bridge Building: Sử dụng các từ nối (transitions) để liên kết các ý rời rạc "
    "thành một dòng chảy thông tin liền mạch.\n\n"
    "Instructions & Rules:\n"
    "1. Phong cách xưng hô: Sử dụng 'Mình - Bạn' hoặc 'Chúng ta' để tạo sự gần gũi "
    "như một người hướng dẫn (mentor).\n"
    "2. Cấu trúc nội dung:\n"
    "   - Mở đầu: Chào hỏi và dẫn dắt vào chủ đề một cách hào hứng.\n"
    "   - Thân bài: Giữ nguyên các mục (Header) từ tài liệu gốc nhưng biến chúng "
    "thành các luận điểm trong lời nói.\n"
    "   - Kết thúc: Tóm tắt ngắn gọn và đưa ra lời chúc hoặc lời khuyên.\n"
    "3. Xử lý thuật ngữ & Ký hiệu (Quan trọng):\n"
    "   - Các thuật ngữ tiếng Anh quan trọng: Giữ nguyên nếu phổ biến, hoặc thêm "
    "chú thích cách đọc nếu cần.\n"
    "   - Biến các dấu gạch đầu dòng (bullet points) thành các câu văn có từ nối "
    "(Ví dụ: 'Thứ nhất là...', 'Điểm tiếp theo cần lưu ý là...').\n"
    "4. Định dạng văn bản: Sử dụng dấu phẩy và dấu chấm để tạo khoảng nghỉ cho "
    "máy đọc. Tránh dùng các ký hiệu lạ mà máy đọc có thể phát âm sai.\n\n"
    "Output Format:\n"
    "- Nội dung kịch bản phải liền mạch.\n"
    "- Không sử dụng các định dạng Markdown phức tạp (như bảng) trong phần kịch bản "
    "vì TTS không đọc được."
)


def load_system_prompt() -> str:
    """Tải System Prompt từ file system_prompt.md nếu có, nếu không trả về prompt mặc định."""
    possible_paths = [
        Path(os.getcwd()) / "system_prompt.md",
        Path(__file__).parent / "system_prompt.md",
        Path(__file__).parent.parent / "system_prompt.md",
        Path(__file__).parent.parent.parent / "system_prompt.md",
        Path(__file__).parent.parent.parent.parent / "system_prompt.md",
    ]
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        print(f"[ScriptEditor] Loaded system prompt from: {path.resolve()}")
                        return content
            except Exception as e:
                print(f"[ScriptEditor] Error reading prompt from {path}: {e}")
    
    print("[ScriptEditor] Using default built-in system prompt")
    return SYSTEM_PROMPT


class ScriptEditor:
    def __init__(self, config: ConfigManager):
        self.config = config

    def _get_client(self) -> OpenAI:
        """Tạo OpenAI client từ config"""
        return OpenAI(
            api_key=self.config.get("api_key"),
            base_url=self.config.get("api_base"),
        )

    def edit(self, web_content: str) -> str:
        """
        Gửi nội dung web lên LLM để biên tập thành audio script.
        """
        client = self._get_client()
        prompt = load_system_prompt()

        try:
            resp = client.chat.completions.create(
                model=self.config.get("model"),
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": (
                        "Hãy biến nội dung tài liệu web sau đây thành một kịch bản audio "
                        "mượt mà, dễ nghe:\n\n" + web_content
                     )}
                ],
                temperature=self.config.get("temperature"),
                max_tokens=self.config.get("max_tokens"),
            )

            script = resp.choices[0].message.content
            return script.strip() if script else "⚠️ LLM không trả về nội dung."

        except Exception as e:
            return f"⚠️ Lỗi khi gọi LLM: {e}"
