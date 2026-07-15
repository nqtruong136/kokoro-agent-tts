"""history_manager.py — Lưu lịch sử fetch, script và audio, tối đa 10 bản mỗi loại cho Server"""

import json
import os
import shutil
from pathlib import Path

MAX_HISTORY = 10

BASE_DIR = Path(__file__).parent.parent
HISTORY_FILE = str(BASE_DIR / "output" / "history.json")
HISTORY_DIR = str(BASE_DIR / "output" / "history")


class HistoryManager:
    def __init__(self):
        self.history = {
            "fetches": [],
            "scripts": [],
            "audio": [],
        }
        Path(HISTORY_DIR).mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """Load history từ file JSON"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.history = {
                        "fetches": saved.get("fetches", []),
                        "scripts": saved.get("scripts", []),
                        "audio": saved.get("audio", []),
                    }
            except Exception:
                self.history = {"fetches": [], "scripts": [], "audio": []}
        else:
            self.history = {"fetches": [], "scripts": [], "audio": []}

    def _save(self):
        """Save history ra file JSON"""
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def add_fetch(self, url: str, title: str, content: str) -> dict:
        """Thêm nội dung đã fetch vào history"""
        item = {
            "id": len(self.history["fetches"]) + 1,
            "url": url,
            "title": title,
            "content": content,
            "preview": content[:100].replace("\n", " ") if content else "",
        }
        self.history["fetches"].insert(0, item)
        if len(self.history["fetches"]) > MAX_HISTORY:
            self.history["fetches"] = self.history["fetches"][:MAX_HISTORY]
        self._save()
        return item

    def get_fetches(self) -> list:
        return self.history.get("fetches", [])

    def get_fetch(self, idx: int) -> dict | None:
        fetches = self.get_fetches()
        if 0 <= idx < len(fetches):
            return fetches[idx]
        return None

    def clear_fetches(self):
        self.history["fetches"] = []
        self._save()

    def add_script(self, url: str, title: str, content: str) -> dict:
        """Thêm script mới đã biên tập bằng LLM vào history"""
        item = {
            "id": len(self.history["scripts"]) + 1,
            "url": url,
            "title": title,
            "content": content,
            "preview": content[:100].replace("\n", " ") if content else "",
        }
        self.history["scripts"].insert(0, item)
        if len(self.history["scripts"]) > MAX_HISTORY:
            self.history["scripts"] = self.history["scripts"][:MAX_HISTORY]
        self._save()
        return item

    def get_scripts(self) -> list:
        return self.history.get("scripts", [])

    def get_script(self, idx: int) -> dict | None:
        scripts = self.get_scripts()
        if 0 <= idx < len(scripts):
            return scripts[idx]
        return None

    def clear_scripts(self):
        self.history["scripts"] = []
        self._save()

    def add_audio(self, source_script: str, audio_path: str) -> dict:
        """Thêm audio vào history và copy file vào thư mục history để lưu lâu dài"""
        audio_id = len(self.history["audio"]) + 1
        ext = os.path.splitext(audio_path)[1] or ".mp3"
        dest_name = f"audio_{audio_id}_{os.path.basename(audio_path)}"
        dest_path = os.path.join(HISTORY_DIR, dest_name)

        try:
            shutil.copy2(audio_path, dest_path)
        except Exception:
            dest_path = audio_path  # fallback

        preview = source_script[:80].replace("\n", " ") if source_script else ""
        item = {
            "id": audio_id,
            "path": dest_path,
            "filename": dest_name,
            "preview": preview,
        }
        self.history["audio"].insert(0, item)

        if len(self.history["audio"]) > MAX_HISTORY:
            removed = self.history["audio"].pop()
            old_path = removed.get("path", "")
            if old_path and os.path.exists(old_path) and old_path.startswith(HISTORY_DIR):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
            self.history["audio"] = self.history["audio"][:MAX_HISTORY]

        self._save()
        return item

    def get_audio_list(self) -> list:
        return self.history.get("audio", [])

    def clear_audio(self):
        for item in self.history.get("audio", []):
            path = item.get("path", "")
            if path and os.path.exists(path) and path.startswith(HISTORY_DIR):
                try:
                    os.remove(path)
                except Exception:
                    pass
        self.history["audio"] = []
        self._save()

    def clear_all(self):
        self.clear_audio()
        self.clear_scripts()
        self.clear_fetches()
