"""kokoro_wrapper.py — Wrapper cho Kokoro-Vietnamese TTS (local inference) cho Server"""

import os
from pathlib import Path
import numpy as np
import soundfile as sf
from src.config_manager import ConfigManager

BASE_DIR = Path(__file__).parent.parent
AUDIO_DIR = BASE_DIR / "output" / "audio_temp"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def clean_text_for_tts(text: str) -> str:
    """Làm sạch văn bản, loại bỏ ký tự đặc biệt/markdown tránh lỗi g2p của Kokoro"""
    # Bước 1: Dùng Normalizer của sea_g2p để chuẩn hoá số, email, tiền tệ
    try:
        from sea_g2p import Normalizer
        normalizer = Normalizer(lang="vi")
        text = normalizer.normalize([text])[0]
        # Xóa thẻ <en></en> do normalizer sinh ra để tránh lỗi KeyError: '<' trong Kokoro
        text = text.replace("<en>", "").replace("</en>", "")
    except ImportError:
        pass

    # Bước 2: Loại bỏ dấu sao markdown ** và *
    t = text.replace("**", "").replace("*", "")
    # Loại bỏ gạch dưới _
    t = t.replace("_", "")
    # Thay thế gạch ngang dài — hoặc -- bằng dấu phẩy hoặc khoảng trắng
    t = t.replace("—", ", ").replace("--", ", ")
    return t


class KokoroWrapper:
    def __init__(self, config: ConfigManager):
        self.config = config
        self._model = None
        self._current_file = None

    def _get_model(self):
        """Lazy-load model (chỉ load khi cần)"""
        if self._model is not None:
            return self._model

        from kokoro_vietnamese import KokoroVietnamese

        device = self.config.get("kokoro_device") or "cpu"
        if device == "cpu":  # Auto-detect CUDA nếu chưa được set
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
            except ImportError:
                pass

        voice = self.config.get("kokoro_voice") or "diem_trinh"

        model_path = self.config.get("kokoro_model_path") or ""
        voicepack_path = self.config.get("kokoro_voicepack_path") or ""
        config_path = self.config.get("kokoro_config_path") or ""

        kwargs = {"device": device, "voice": voice}
        
        if voice == "custom_voice":
            voicepack_dir = os.path.join(BASE_DIR, "voicepacks")
            local_custom_path = None
            if os.path.exists(voicepack_dir):
                pt_files = [f for f in os.listdir(voicepack_dir) if f.startswith("custom_voice") and f.endswith(".pt")]
                if pt_files:
                    pt_files.sort()  # Sắp xếp để lấy file có chỉ số bước hoặc điểm cao nhất
                    local_custom_path = os.path.join(voicepack_dir, pt_files[-1])
            
            if local_custom_path and os.path.exists(local_custom_path):
                kwargs["voicepack_path"] = local_custom_path
                kwargs["voice"] = "diem_trinh"  # Dummy voice để tránh lỗi KeyError của thư viện gốc
                print(f"[KokoroWrapper] Đang nạp giọng custom từ: {local_custom_path}")
            else:
                print(f"[KokoroWrapper] Cảnh báo: Không tìm thấy file custom_voice dạng .pt tại {voicepack_dir}, dùng diem_trinh.")
                kwargs["voice"] = "diem_trinh"

        # Tự động định tuyến sang file voicepack cục bộ nếu có trong model/voicepacks
        if voice != "custom_voice":
            local_vp = os.path.join(BASE_DIR, "model", "voicepacks", f"{voice}.pt")
            if os.path.exists(local_vp):
                kwargs["voicepack_path"] = local_vp
            elif voicepack_path and os.path.exists(voicepack_path):
                kwargs["voicepack_path"] = voicepack_path
        
        if model_path and os.path.exists(model_path):
            kwargs["model_path"] = model_path
        if config_path and os.path.exists(config_path):
            kwargs["config_path"] = config_path

        self._model = KokoroVietnamese(**kwargs)
        return self._model

    def _split_text(self, text: str, max_chars: int = 500) -> list:
        """
        Tách văn bản thành các đoạn nhỏ dưới max_chars để không bị vượt quá giới hạn 510 phonemes.
        Giữ câu nguyên vẹn tối đa, chỉ ngắt câu khi thật sự vượt quá max_chars.
        """
        import re
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        
        chunks = []
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            sentences = re.split(r'(?<=[.?!;])\s+', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                if len(sentence) > max_chars:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        current_len = 0
                    
                    sub_sentences = re.split(r'(?<=,)\s+', sentence)
                    for sub in sub_sentences:
                        sub = sub.strip()
                        if not sub:
                            continue
                        
                        if len(sub) > max_chars:
                            words = sub.split(" ")
                            temp_words = []
                            temp_len = 0
                            for w in words:
                                if temp_len + len(w) + 1 > max_chars:
                                    if temp_words:
                                        chunks.append(" ".join(temp_words))
                                    temp_words = [w]
                                    temp_len = len(w)
                                else:
                                    temp_words.append(w)
                                    temp_len += len(w) + 1
                            if temp_words:
                                chunks.append(" ".join(temp_words))
                        else:
                            if current_len + len(sub) + 1 > max_chars:
                                if current_chunk:
                                    chunks.append(" ".join(current_chunk))
                                current_chunk = [sub]
                                current_len = len(sub)
                            else:
                                current_chunk.append(sub)
                                current_len += len(sub) + 1
                else:
                    if current_len + len(sentence) + 1 > max_chars:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_len = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_len += len(sentence) + 1
            
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        valid_chunks = []
        for c in chunks:
            c_clean = c.strip()
            if len(c_clean) > 2 and any(char.isalnum() for char in c_clean):
                valid_chunks.append(c_clean)
                
        return valid_chunks

    def generate_audio(self, text: str) -> str:
        """Synthesize text thành WAV file (chia chunk thông minh). Returns path."""
        model = self._get_model()

        import uuid
        filename = f"kokoro_{uuid.uuid4().hex[:8]}.wav"
        output_path = str(AUDIO_DIR / filename)

        cleaned_text = clean_text_for_tts(text)
        chunks = self._split_text(cleaned_text, max_chars=250)
        if not chunks:
            raise RuntimeError("Văn bản rỗng hoặc không có nội dung để tổng hợp")

        audio_parts = []
        phoneme_parts = []
        for chunk in chunks:
            try:
                audio_chunk, phonemes = model.synthesize(chunk)
                audio_parts.append(audio_chunk)
                phoneme_parts.append(phonemes)
            except Exception as e:
                print(f"[KokoroWrapper] Lỗi khi tổng hợp chunk '{chunk[:30]}...': {e}")
                raise RuntimeError(f"Lỗi tổng hợp đoạn văn: {e}")

        # Sử dụng/Hiển thị phonemes cho dự án
        full_phonemes = " | ".join(phoneme_parts)
        print(f"\\n[Kokoro Phonemes] {full_phonemes}\\n")

        if not audio_parts:
            raise RuntimeError("Không thể tổng hợp bất kỳ âm thanh nào từ văn bản")

        if len(audio_parts) == 1:
            final_audio = audio_parts[0]
        else:
            final_audio = np.concatenate(audio_parts)

        sf.write(output_path, final_audio, 24000)

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Kokoro không tạo được file audio")

        self._current_file = output_path
        return output_path

    def get_available_voices(self) -> list:
        return [
            "diem_trinh", "hung_thinh", "mai_linh", "mai_loan",
            "manh_dung", "my_yen", "ngoc_huyen", "phat_tai",
            "thanh_dat", "thuc_trinh", "tuan_ngoc", "storyvert",
            "duc_an", "duc_duy",
            "custom_voice",
        ]

    def cleanup(self):
        self._model = None
