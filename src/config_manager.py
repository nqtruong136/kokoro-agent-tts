"""config_manager.py — Quản lý cấu hình LLM (OpenAI-compatible) cho Server"""

import json
import os

# Thư mục server (web-to-audio-server/)
_SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Thư mục app desktop (web-to-audio-app/) nằm cạnh thư mục server
_APP_DIR = os.path.join(os.path.dirname(_SERVER_DIR), "web-to-audio-app")

# Ưu tiên đọc từ server trước, fallback sang app desktop nếu không tìm thấy
_SERVER_CONFIG = os.path.join(_SERVER_DIR, "config.json")
_APP_CONFIG = os.path.join(_APP_DIR, "config.json")

# File để GHI luôn là của server để không ghi đè app
CONFIG_FILE = _SERVER_CONFIG

DEFAULT_CONFIG = {
    "api_base": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 4096,
    "tts_engine": "edge-tts",         # "edge-tts" | "kokoro"
    "tts_voice": "vi-VN-HoaiMyNeural",
    "kokoro_voice": "diem_trinh",
    "kokoro_device": "cpu",
}


class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    @property
    def config_path(self):
        return CONFIG_FILE

    def load(self):
        """Load config tu file JSON.

        Uu tien:
        1. config.json cua server (web-to-audio-server/config.json)
        2. config.json cua desktop app (web-to-audio-app/config.json)
        3. Gia tri mac dinh (DEFAULT_CONFIG)
        """
        loaded = False
        for candidate in [_SERVER_CONFIG, _APP_CONFIG]:
            if os.path.exists(candidate):
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                        self.config = {**DEFAULT_CONFIG, **saved}
                    loaded = True
                    print(f"[ConfigManager] Da nap cau hinh tu: {candidate}")
                    break
                except Exception as e:
                    print(f"[ConfigManager] Loi doc {candidate}: {e}")
        if not loaded:
            self.config = DEFAULT_CONFIG.copy()
            print("[ConfigManager] Dung cau hinh mac dinh (khong tim thay config.json)")

    def save(self):
        """Save config ra file JSON cua server"""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key: str):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value):
        self.config[key] = value
        self.save()
