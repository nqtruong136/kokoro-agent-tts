"""tts_engine.py — TTS engine routing (edge-tts / Kokoro-Vietnamese) cho Server"""

import asyncio
import os
from pathlib import Path
import threading
import edge_tts
from src.config_manager import ConfigManager

BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "output" / "audio_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class TTSEngine:
    def __init__(self, config: ConfigManager):
        self.config = config
        self._kokoro = None
        self._current_file = None
        self._lock = threading.Lock()

    @property
    def _engine_type(self) -> str:
        """Trả về 'edge-tts' hoặc 'kokoro' theo config"""
        return self.config.get("tts_engine") or "edge-tts"

    @property
    def _kokoro_wrapper(self):
        """Lazy-load KokoroWrapper"""
        if self._kokoro is None and self._engine_type == "kokoro":
            from src.kokoro_wrapper import KokoroWrapper
            self._kokoro = KokoroWrapper(self.config)
        return self._kokoro

    @property
    def voice(self) -> str:
        if self._engine_type == "kokoro":
            return self.config.get("kokoro_voice") or "diem_trinh"
        return self.config.get("tts_voice") or "vi-VN-HoaiMyNeural"

    @voice.setter
    def voice(self, value: str):
        if self._engine_type == "kokoro":
            self.config.set("kokoro_voice", value)
        else:
            self.config.set("tts_voice", value)

    def _run_async(self, coro):
        """Run async function trong sync context"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    @staticmethod
    def _clean_text_for_tts(text: str) -> str:
        """Làm sạch text trước khi gửi cho edge-tts"""
        import re
        clean = re.sub(
            r'[^\w\s\.\,\!\?\:\;\-\/\(\)\[\]\{\}\"\'@#\$%\^&\*\+\=\~\`\|\\<>]',
            '',
            text,
            flags=re.UNICODE
        )
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def generate_audio(self, text: str) -> str:
        """Tạo audio file từ text. Returns: path đến file audio."""
        with self._lock:
            if self._engine_type == "kokoro":
                return self._kokoro_wrapper.generate_audio(text)

        # edge-tts path
        cleaned_text = self._clean_text_for_tts(text)
        if not cleaned_text.strip():
            raise RuntimeError("Text rỗng sau khi làm sạch")

        import uuid
        filename = f"edge_{uuid.uuid4().hex[:8]}.mp3"
        output_file = str(TEMP_DIR / filename)

        async def _generate():
            communicate = edge_tts.Communicate(cleaned_text, self.voice)
            await communicate.save(output_file)

        self._run_async(_generate())
        self._current_file = output_file

        if not os.path.exists(output_file):
            raise RuntimeError("edge-tts không tạo được file audio")
        if os.path.getsize(output_file) == 0:
            raise RuntimeError("edge-tts tạo file rỗng")

        return output_file
