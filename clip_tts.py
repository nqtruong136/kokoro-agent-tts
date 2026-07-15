"""clip_tts.py — Quick TTS Player with Interactive CLI TUI (Gemini-style)

Chạy: clip_tts.bat hoặc python clip_tts.py [văn bản tùy chọn]
- Không truyền tham số: Hiển thị menu tương tác, đọc từ Clipboard
- Truyền tham số: Đọc trực tiếp văn bản và vào trình phát audio
"""

import os
import sys
import io
import re
import time
import ctypes
import threading
import msvcrt
import requests
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════════════════════════

# Enable ANSI Virtual Terminal Processing on Windows 10+
_kernel32 = ctypes.windll.kernel32
_handle = _kernel32.GetStdHandle(ctypes.c_ulong(-11))  # STD_OUTPUT_HANDLE
_mode = ctypes.c_ulong()
_kernel32.GetConsoleMode(_handle, ctypes.byref(_mode))
_kernel32.SetConsoleMode(_handle, _mode.value | 0x0004)

# UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

ROOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

TEMP_DIR = ROOT_DIR / "output" / "audio_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def log_debug(msg: str):
    try:
        with open(ROOT_DIR / "debug_tui.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════
# GEMINI-STYLE COLOR PALETTE (ANSI 24-bit RGB)
# ══════════════════════════════════════════════════════════════

class C:
    """Bảng màu Gemini với hiệu ứng gradient xanh-tím-lam."""
    RST   = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"
    ITAL  = "\033[3m"
    ULINE = "\033[4m"

    # Foreground — Gemini palette
    BLUE   = "\033[38;2;66;133;244m"
    PURPLE = "\033[38;2;168;85;247m"
    VIOLET = "\033[38;2;124;77;255m"
    CYAN   = "\033[38;2;0;188;212m"
    GREEN  = "\033[38;2;52;168;83m"
    YELLOW = "\033[38;2;251;188;5m"
    RED    = "\033[38;2;234;67;53m"
    WHITE  = "\033[38;2;220;220;230m"
    GRAY   = "\033[38;2;110;110;130m"
    LGRAY  = "\033[38;2;160;160;175m"

    # Bright accents
    NEON_BLUE   = "\033[38;2;100;180;255m"
    NEON_PURPLE = "\033[38;2;190;120;255m"
    NEON_CYAN   = "\033[38;2;80;230;230m"

    # Background highlights
    BG_SELECT = "\033[48;2;45;35;75m"
    BG_BAR    = "\033[48;2;30;30;50m"

_ANSI_RE = re.compile(r'\033\[[^m]*m')

def vlen(s: str) -> int:
    """Chiều dài thật (visible) của chuỗi sau khi bỏ ANSI codes."""
    return len(_ANSI_RE.sub('', s))


# ══════════════════════════════════════════════════════════════
# TERMINAL UTILITIES
# ══════════════════════════════════════════════════════════════

def clear():
    """Xoá màn hình bằng ANSI (nhanh hơn os.system('cls'))."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def reset_cursor():
    """Di chuyển con trỏ về góc trên bên trái không xóa màn hình (tránh nhấp nháy UI)."""
    sys.stdout.write("\033[H")
    sys.stdout.flush()

def clean_lines(parts: list[str]) -> str:
    """Ghép các dòng lại và thêm mã ANSI \033[K để xóa các chữ thừa cũ ở cuối dòng."""
    return "\n".join(f"{line}\033[K" for line in parts) + "\033[J"

def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def get_key():
    """Đọc phím không chặn (non-blocking). Trả về tên phím hoặc None."""
    if not msvcrt.kbhit():
        return None
    ch = msvcrt.getch()
    if ch in (b'\xe0', b'\x00'):
        ch2 = msvcrt.getch()
        return {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right'}.get(ch2)
    return {
        b'\r': 'enter', b' ': 'space', b'\x1b': 'esc',
        b'q': 'esc', b'Q': 'esc',
        b'+': 'plus', b'=': 'plus',
        b'-': 'minus', b'_': 'minus',
    }.get(ch)

def wait_key():
    """Chờ và trả về phím (blocking)."""
    while True:
        k = get_key()
        if k:
            return k
        time.sleep(0.03)

def flush_input():
    """Xóa sạch toàn bộ phím đang đệm trong bộ nhớ để tránh trôi phím."""
    while msvcrt.kbhit():
        msvcrt.getch()


# ══════════════════════════════════════════════════════════════
# CLIPBOARD (Windows ctypes — không cần thư viện ngoài)
# ══════════════════════════════════════════════════════════════

def get_clipboard_text() -> str:
    import ctypes
    from ctypes import wintypes
    
    CF_UNICODETEXT = 13
    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32
    
    # Định nghĩa kiểu dữ liệu (đặc biệt quan trọng trên Windows 64-bit để tránh trôi/cắt con trỏ)
    u32.OpenClipboard.argtypes = [wintypes.HWND]
    u32.OpenClipboard.restype = wintypes.BOOL
    
    u32.GetClipboardData.argtypes = [wintypes.UINT]
    u32.GetClipboardData.restype = wintypes.HANDLE
    
    k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalLock.restype = wintypes.LPVOID
    
    k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalUnlock.restype = wintypes.BOOL
    
    u32.CloseClipboard.argtypes = []
    u32.CloseClipboard.restype = wintypes.BOOL
    
    if not u32.OpenClipboard(None):
        return ""
    try:
        h = u32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return ""
        src = k32.GlobalLock(h)
        if not src:
            return ""
        try:
            return ctypes.c_wchar_p(src).value or ""
        finally:
            k32.GlobalUnlock(h)
    finally:
        u32.CloseClipboard()


# ══════════════════════════════════════════════════════════════
# MCI AUDIO PLAYER (Windows built-in — không cần pygame)
# ══════════════════════════════════════════════════════════════

class MCIPlayer:
    """Bọc Windows MCI cho playback WAV/MP3 với seek & position."""

    def __init__(self):
        self._alias = "cliptts"
        self._open = False
        self._wm = ctypes.windll.winmm

    def _cmd(self, command: str):
        buf = ctypes.create_unicode_buffer(512)
        err = self._wm.mciSendStringW(command, buf, 511, 0)
        return buf.value, err

    def open(self, path: str) -> bool:
        if self._open:
            self.close()
        p = str(path).replace("\\", "/")
        _, err = self._cmd(f'open "{p}" alias {self._alias}')
        if err == 0:
            self._open = True
            self._cmd(f'set {self._alias} time format milliseconds')
        return err == 0

    def play(self, from_ms: int | None = None):
        if from_ms is not None:
            self._cmd(f'seek {self._alias} to {max(0, int(from_ms))}')
        self._cmd(f'play {self._alias}')

    def pause(self):
        self._cmd(f'pause {self._alias}')

    def resume(self):
        self._cmd(f'resume {self._alias}')

    def stop(self):
        self._cmd(f'stop {self._alias}')

    def seek(self, ms: int):
        was_playing = self.mode() == "playing"
        self._cmd(f'seek {self._alias} to {max(0, int(ms))}')
        if was_playing:
            self._cmd(f'play {self._alias}')

    def position(self) -> int:
        v, _ = self._cmd(f'status {self._alias} position')
        try:
            return int(v)
        except ValueError:
            return 0

    def length(self) -> int:
        v, _ = self._cmd(f'status {self._alias} length')
        try:
            return int(v)
        except ValueError:
            return 0

    def mode(self) -> str:
        v, _ = self._cmd(f'status {self._alias} mode')
        return v.lower().strip()

    def close(self):
        if self._open:
            self._cmd(f'stop {self._alias}')
            self._cmd(f'close {self._alias}')
            self._open = False


# ══════════════════════════════════════════════════════════════
# WAV SPEED CONTROL (thay đổi sample rate → tốc độ phát)
# ══════════════════════════════════════════════════════════════

SPEEDS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

def _nearest_speed_idx(speed: float) -> int:
    return min(range(len(SPEEDS)), key=lambda i: abs(SPEEDS[i] - speed))

def create_speed_wav(original_path: str, speed: float) -> str:
    """Ghi lại WAV với sample rate mới = sr * speed → phát nhanh/chậm.
    Trả về đường dẫn file tạm."""
    import soundfile as sf
    data, sr = sf.read(original_path)
    new_sr = int(sr * speed)
    tag = f"{speed:.2f}".replace(".", "")
    out = str(TEMP_DIR / f"_spd_{tag}.wav")
    sf.write(out, data, new_sr)
    return out


# ══════════════════════════════════════════════════════════════
# TTS GENERATION
# ══════════════════════════════════════════════════════════════

SERVER_URL = "http://localhost:8000"

def check_server() -> bool:
    import socket
    try:
        # Thay thế requests bằng socket để tránh bị treo do cài đặt Proxy trên máy
        s = socket.create_connection(("127.0.0.1", 8000), timeout=0.5)
        s.close()
        return True
    except Exception:
        return False

def generate_tts_server(text: str) -> str:
    r = requests.post(f"{SERVER_URL}/api/tts", json={"script": text}, timeout=120)
    r.raise_for_status()
    fn = r.json().get("filename")
    local = ROOT_DIR / "output" / "history" / fn
    if local.exists():
        return str(local)
    dl = requests.get(f"{SERVER_URL}/audio/history/{fn}", timeout=15)
    dl.raise_for_status()
    p = TEMP_DIR / fn
    p.write_bytes(dl.content)
    return str(p)

# Cache engine toàn cục để không phải nạp model mỗi lần
_local_engine = None
_local_cfg = None

def generate_tts_local(text: str) -> str:
    global _local_engine, _local_cfg
    if _local_engine is None:
        from src.config_manager import ConfigManager
        from src.tts_engine import TTSEngine
        _local_cfg = ConfigManager()
        _local_engine = TTSEngine(_local_cfg)
    return _local_engine.generate_audio(text)

def invalidate_local_engine():
    """Xoá cache engine khi user đổi cấu hình."""
    global _local_engine, _local_cfg
    _local_engine = None
    _local_cfg = None


# ══════════════════════════════════════════════════════════════
# UI RENDERING FUNCTIONS
# ══════════════════════════════════════════════════════════════

def fmt_time(ms: int) -> str:
    s = max(0, ms) // 1000
    return f"{s // 60:02d}:{s % 60:02d}"

# ─── Gradient Title ───
def _gradient_title() -> str:
    """Tiêu đề gradient xanh → tím → lam kiểu Gemini."""
    parts = [
        (C.NEON_BLUE, "✦ "),
        (C.BLUE,      "W"),
        (C.BLUE,      "E"),
        (C.BLUE,      "B"),
        (C.VIOLET,    "-"),
        (C.VIOLET,    "T"),
        (C.PURPLE,    "O"),
        (C.PURPLE,    "-"),
        (C.NEON_PURPLE, "A"),
        (C.NEON_PURPLE, "U"),
        (C.NEON_PURPLE, "D"),
        (C.CYAN,      "I"),
        (C.CYAN,      "O"),
        (C.NEON_CYAN, " "),
        (C.NEON_CYAN, "Q"),
        (C.CYAN,      "U"),
        (C.CYAN,      "I"),
        (C.BLUE,      "C"),
        (C.BLUE,      "K"),
        (C.VIOLET,    " "),
        (C.VIOLET,    "T"),
        (C.PURPLE,    "T"),
        (C.NEON_PURPLE, "S"),
        (C.NEON_CYAN, " ✦"),
    ]
    return C.BOLD + "".join(c + t for c, t in parts) + C.RST

def render_header() -> str:
    """Vẽ header gradient không có viền hộp, tối giản và hiện đại."""
    title = _gradient_title()
    border = f"{C.VIOLET}────────────────────────────────────────────────────────{C.RST}"
    return f"\n  {title}\n  {border}"

# ─── Main Menu ───
MENU_ITEMS = [
    ("📋", "Đọc Clipboard & Phát Audio"),
    ("🎙️", "Cấu hình giọng đọc & tốc độ"),
    ("🚪", "Thoát chương trình"),
]

def render_main_menu(sel: int, server_on: bool) -> str:
    parts = []
    parts.append(render_header())
    parts.append("")
    
    for i, (ico, label) in enumerate(MENU_ITEMS):
        if i == sel:
            parts.append(f"  {C.NEON_CYAN}┃{C.RST}  {C.NEON_CYAN}{C.BOLD}{ico}  {label}{C.RST}")
        else:
            parts.append(f"  {C.GRAY}│{C.RST}  {C.LGRAY}{ico}  {label}{C.RST}")
            
    parts.append("")
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    
    # Status bar
    dot = f"{C.GREEN}● Online{C.RST}" if server_on else f"{C.RED}○ Offline{C.RST}"
    parts.append(f"  {C.GRAY}Server Status: {dot}{C.RST}")
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    parts.append(f"  {C.DIM}{C.LGRAY} [↑/↓] Di chuyển   [Enter] Chọn   [Esc] Thoát{C.RST}")
    parts.append("")
    return clean_lines(parts)

# ─── Loading Spinner ───
_SPIN = "⣾⣽⣻⢿⡿⣟⣯⣷"

def render_loading(msg: str, frame: int) -> str:
    s = _SPIN[frame % len(_SPIN)]
    dots = "." * ((frame // 2) % 4)
    parts = []
    parts.append(render_header())
    parts.append("")
    parts.append(f"  {C.NEON_PURPLE}{s}{C.RST}  {C.WHITE}{msg}{C.RST}{C.DIM}{C.GRAY}{dots}{C.RST}")
    parts.append("")
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    parts.append(f"  {C.DIM}{C.LGRAY} [Esc] Hủy bỏ{C.RST}")
    parts.append("")
    return clean_lines(parts)

# ─── Message Box ───
def render_message(icon: str, msg: str, color: str = C.YELLOW) -> str:
    parts = []
    parts.append(render_header())
    parts.append("")
    
    # Wrap text cleanly
    max_w = 54
    words = msg.split()
    lines_text = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > max_w:
            lines_text.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines_text.append(cur)
        
    for i, lt in enumerate(lines_text):
        prefix = f"  {icon} " if i == 0 else "     "
        parts.append(f"{color}{prefix}{lt}{C.RST}")
        
    parts.append("")
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    parts.append(f"  {C.DIM}{C.LGRAY} Nhấn phím bất kỳ để tiếp tục...{C.RST}")
    parts.append("")
    return clean_lines(parts)

# ─── Progress Bar ───
def _progress_bar(ratio: float, width: int = 24) -> str:
    filled = int(width * ratio)
    filled = max(0, min(width, filled))
    bar = f"{C.NEON_CYAN}{'━' * filled}{C.NEON_PURPLE}●{C.GRAY}{'─' * (width - filled)}{C.RST}"
    return bar

# ─── Player ───
def render_player(preview: str, pos_ms: int, total_ms: int,
                  speed: float, paused: bool, hist_info: str) -> str:
    ratio = min(1.0, max(0.0, pos_ms / total_ms)) if total_ms > 0 else 0.0
    pct = int(ratio * 100)
    
    if len(preview) > 50:
        preview = preview[:47] + "..."
        
    if paused:
        status_text = f"{C.YELLOW}⏸ TẠM DỪNG{C.RST}"
    else:
        status_text = f"{C.GREEN}▶ ĐANG PHÁT{C.RST}"
        
    spd_color = C.NEON_CYAN if abs(speed - 1.0) > 0.01 else C.LGRAY
    spd_str = f"{spd_color}{speed:.2f}x{C.RST}"
    
    parts = []
    parts.append(render_header())
    parts.append("")
    parts.append(f"  📄  {C.BOLD}Văn bản:{C.RST} {C.ITAL}{C.WHITE}\"{preview}\"{C.RST}")
    parts.append("")
    parts.append(f"  {status_text}   {C.GRAY}│{C.RST}   Tốc độ: {spd_str}")
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    
    bar = _progress_bar(ratio)
    parts.append(f"  {bar}  {C.WHITE}{C.BOLD}{pct:3d}%{C.RST}")
    parts.append(f"  {C.LGRAY}{fmt_time(pos_ms)} / {fmt_time(total_ms)}{C.RST}")
    parts.append("")
    
    if hist_info:
        parts.append(f"  {C.DIM}{C.NEON_PURPLE}{hist_info}{C.RST}")
    else:
        parts.append("")
        
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    parts.append(f"  {C.DIM}{C.LGRAY} [Space] Phát/Dừng   [←/→] Tua ±5s   [+/-] Tốc độ (WAV){C.RST}")
    parts.append(f"  {C.DIM}{C.LGRAY} [↑/↓] Lịch sử       [Enter] Lại đầu [Esc] Menu chính{C.RST}")
    parts.append("")
    return clean_lines(parts)

# ─── Settings ───
KOKORO_VOICES = [
    "diem_trinh", "hung_thinh", "mai_linh", "mai_loan",
    "manh_dung", "my_yen", "ngoc_huyen", "phat_tai",
    "thanh_dat", "thuc_trinh", "tuan_ngoc", "storyvert",
    "duc_an", "duc_duy", "custom_voice",
]
EDGE_VOICES = ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]
ENGINES = ["kokoro", "edge-tts"]

def render_settings(sel: int, engine: str, voice: str, def_speed: float) -> str:
    items = [
        ("Công cụ TTS", engine.upper()),
        ("Giọng mặc định", voice),
        ("Tốc độ mặc định", f"{def_speed:.2f}x"),
    ]
    
    parts = []
    parts.append(render_header())
    parts.append("")
    
    for i, (label, value) in enumerate(items):
        if i == sel:
            parts.append(f"  {C.NEON_CYAN}┃{C.RST}  {C.NEON_CYAN}{C.BOLD}{label:<18}: ◄ [ {value} ] ►{C.RST}")
        else:
            parts.append(f"  {C.GRAY}│{C.RST}  {C.LGRAY}{label:<18}:   [ {value} ]{C.RST}")
            
    parts.append("")
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    
    if sel == 3:
        parts.append(f"  {C.NEON_CYAN}┃{C.RST}  {C.NEON_CYAN}{C.BOLD}↩  Quay lại Menu chính{C.RST}")
    else:
        parts.append(f"  {C.GRAY}│{C.RST}  {C.LGRAY}↩  Quay lại Menu chính{C.RST}")
        
    parts.append(f"{C.VIOLET}  ────────────────────────────────────────────────────────{C.RST}")
    parts.append(f"  {C.DIM}{C.LGRAY} [↑/↓] Chọn mục   [←/→] Đổi giá trị   [Esc] Quay lại{C.RST}")
    parts.append("")
    return clean_lines(parts)


# ══════════════════════════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.mci = MCIPlayer()
        self.history: list[dict] = []   # [{text, preview, audio_file}, ...]
        self.history_idx = -1
        self.default_speed = 1.0
        self.engine = "kokoro"
        self.voice = "hung_thinh"
        self._server_on = False
        self._load_config()

    # ─── Config ───
    def _load_config(self):
        try:
            from src.config_manager import ConfigManager
            cfg = ConfigManager()
            self.engine = cfg.get("tts_engine") or "kokoro"
            self.voice = (cfg.get("kokoro_voice") if self.engine == "kokoro"
                          else cfg.get("tts_voice")) or "hung_thinh"
        except Exception:
            pass

    def _save_config(self):
        try:
            from src.config_manager import ConfigManager
            cfg = ConfigManager()
            cfg.set("tts_engine", self.engine)
            if self.engine == "kokoro":
                cfg.set("kokoro_voice", self.voice)
            else:
                cfg.set("tts_voice", self.voice)
        except Exception:
            pass

    # ─── Entry Point ───
    def run(self):
        log_debug("App.run() started")
        log_debug(f"Command line args: {sys.argv}")
        
        # Kiểm tra cờ non-interactive
        non_interactive = False
        if "--non-interactive" in sys.argv:
            non_interactive = True
            sys.argv.remove("--non-interactive")
            
        try:
            if not non_interactive:
                hide_cursor()
                # Chuyển sang alternate screen buffer để ẩn thanh cuộn và làm sạch giao diện như các CLI hiện đại
                sys.stdout.write("\033[?1049h\033[H")
                sys.stdout.flush()
                
            # Nếu có tham số dòng lệnh → phát trực tiếp
            if len(sys.argv) > 1:
                # Hỗ trợ cờ --input-file nếu được truyền vào
                if "--input-file" in sys.argv:
                    try:
                        idx = sys.argv.index("--input-file")
                        arg_text = sys.argv[idx + 1].strip()
                    except (ValueError, IndexError):
                        arg_text = ""
                else:
                    arg_text = " ".join(sys.argv[1:]).strip()

                # Kiểm tra xem có phải là đường dẫn file không
                if arg_text and os.path.isfile(arg_text):
                    try:
                        with open(arg_text, "r", encoding="utf-8") as f:
                            text = f.read().strip()
                        log_debug(f"Loaded text from file: {arg_text} ({len(text)} chars)")
                    except Exception as e:
                        text = arg_text
                        log_debug(f"Failed to read file {arg_text}, fallback to raw: {e}")
                else:
                    text = arg_text

                if text:
                    self._server_on = check_server()
                    log_debug(f"Direct mode - server_on: {self._server_on}, non_interactive: {non_interactive}")
                    if non_interactive:
                        self._play_non_interactive(text)
                    else:
                        self._generate_and_play(text)
            else:
                if non_interactive:
                    log_debug("Error: --non-interactive requires input text or file.")
                else:
                    log_debug("No arguments, entering main_menu_loop()")
                    self.main_menu_loop()
        except KeyboardInterrupt:
            log_debug("KeyboardInterrupt in App.run()")
        finally:
            log_debug("finally block in App.run() started")
            self.mci.close()
            if not non_interactive:
                # Khôi phục lại screen buffer ban đầu của Terminal
                sys.stdout.write("\033[?1049l")
                sys.stdout.flush()
                show_cursor()
                clear()
                print(f"{C.GRAY}👋 Tạm biệt!{C.RST}")
            log_debug("App.run() ended")

    def _play_non_interactive(self, text: str):
        log_debug(f"_play_non_interactive() started with text length: {len(text)}")
        try:
            # 1. Sinh âm thanh
            if self._server_on:
                audio_file = generate_tts_server(text)
            else:
                audio_file = generate_tts_local(text)
            
            if not audio_file or not os.path.exists(audio_file):
                log_debug("Failed to generate audio file in non-interactive mode")
                return
                
            log_debug(f"Non-interactive generated: {audio_file}")
            
            # 2. Phát âm thanh bằng MCIPlayer
            speed = self.default_speed
            current_file = audio_file
            is_wav = audio_file.lower().endswith(".wav")
            if is_wav and abs(speed - 1.0) > 0.01:
                try:
                    current_file = create_speed_wav(audio_file, speed)
                except Exception as e:
                    log_debug(f"Failed to create speed WAV: {e}")
                    current_file = audio_file

            if not self.mci.open(current_file):
                log_debug("Failed to open audio file in non-interactive mode")
                return
                
            self.mci.play()
            log_debug("Non-interactive playback started")
            
            # 3. Đợi cho đến khi phát xong
            while True:
                time.sleep(0.1)
                mode = self.mci.mode()
                pos = self.mci.position()
                total = self.mci.length()
                if mode == "stopped" or (total > 0 and pos >= total - 50):
                    break
                    
            log_debug("Non-interactive playback finished successfully")
        except Exception as e:
            log_debug(f"Error in non-interactive playback: {e}")

    # ─── Main Menu ───
    def main_menu_loop(self):
        log_debug("main_menu_loop() started")
        sel = 0
        self._server_on = check_server()
        log_debug(f"main_menu_loop - check_server returned: {self._server_on}")

        clear()
        while True:
            reset_cursor()
            print(render_main_menu(sel, self._server_on))

            key = wait_key()
            if key == 'up':
                sel = (sel - 1) % len(MENU_ITEMS)
            elif key == 'down':
                sel = (sel + 1) % len(MENU_ITEMS)
            elif key == 'enter':
                if sel == 0:
                    self._clipboard_flow()
                elif sel == 1:
                    self.settings_loop()
                elif sel == 2:
                    break
            elif key == 'esc':
                break

    # ─── Clipboard → TTS → Player ───
    def _clipboard_flow(self):
        log_debug("_clipboard_flow() started")
        text = get_clipboard_text().strip()
        log_debug(f"get_clipboard_text returned {len(text)} characters")
        if not text:
            log_debug("Clipboard empty, showing warning")
            clear()
            print(render_message("⚠️", "Clipboard trống hoặc không chứa văn bản!", C.YELLOW))
            flush_input()
            wait_key()
            return
        self._generate_and_play(text)

    def _generate_and_play(self, text: str):
        log_debug(f"_generate_and_play() started with text length: {len(text)}")
        preview = text.replace('\n', ' ')
        preview = preview if len(preview) <= 80 else preview[:77] + "..."

        # Background TTS generation
        result = {"file": None, "error": None}
        done = threading.Event()

        def worker():
            log_debug("worker() thread running")
            try:
                if self._server_on:
                    log_debug("worker() calling generate_tts_server")
                    result["file"] = generate_tts_server(text)
                else:
                    log_debug("worker() calling generate_tts_local")
                    result["file"] = generate_tts_local(text)
                log_debug(f"worker() succeeded: {result['file']}")
            except Exception as e:
                import traceback
                err_str = traceback.format_exc()
                result["error"] = str(e)
                log_debug(f"worker() failed with exception:\n{err_str}")
            finally:
                done.set()

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        log_debug("worker() thread started")

        # Loading animation
        msg = "Gửi tới Server (siêu tốc)..." if self._server_on else "Khởi tạo TTS offline..."
        frame = 0
        clear()
        while not done.is_set():
            reset_cursor()
            print(render_loading(msg, frame))
            frame += 1
            # Kiểm tra Esc để huỷ
            k = get_key()
            if k == 'esc':
                log_debug("User pressed ESC during loading spinner, cancelling")
                return
            time.sleep(0.12)

        log_debug(f"Loading animation finished. error: {result['error']}, file: {result['file']}")
        if result["error"]:
            clear()
            print(render_message("❌", f"Lỗi TTS: {result['error']}", C.RED))
            flush_input()
            wait_key()
            return

        # Thêm vào history
        self.history.append({
            "text": text,
            "preview": preview,
            "audio_file": result["file"],
        })
        self.history_idx = len(self.history) - 1

        # Vào Player
        self._player_loop()

    # ─── Interactive Player ───
    def _player_loop(self):
        log_debug("_player_loop() started")
        if self.history_idx < 0:
            log_debug("history_idx < 0, returning")
            return

        item = self.history[self.history_idx]
        audio_src = item["audio_file"]         # File gốc (không đổi tốc độ)
        preview = item["preview"]
        log_debug(f"_player_loop - audio_src: {audio_src}")
        if not audio_src:
            log_debug("audio_src is None/empty!")
            return
            
        is_wav = audio_src.lower().endswith(".wav")
        speed = self.default_speed
        current_file = audio_src

        # Áp dụng tốc độ nếu khác 1.0 và là WAV
        if is_wav and abs(speed - 1.0) > 0.01:
            try:
                log_debug(f"is_wav is True and speed is {speed}, creating speed WAV")
                current_file = create_speed_wav(audio_src, speed)
                log_debug(f"Speed WAV created: {current_file}")
            except Exception as e:
                import traceback
                log_debug(f"Failed to create speed WAV: {e}\n{traceback.format_exc()}")
                current_file = audio_src
                speed = 1.0

        log_debug(f"Calling mci.open with: {current_file}")
        if not self.mci.open(current_file):
            log_debug("mci.open() failed!")
            clear()
            print(render_message("❌", "Không thể mở file âm thanh!", C.RED))
            flush_input()
            wait_key()
            return
            
        log_debug("mci.open() succeeded, playing audio")
        self.mci.play()
        paused = False

        clear()
        while True:
            # Lấy vị trí phát và tổng thời lượng
            pos = self.mci.position()
            total = self.mci.length()
            mode = self.mci.mode()

            # Chuyển đổi sang thời gian gốc nếu đã thay đổi tốc độ
            if is_wav and abs(speed - 1.0) > 0.01:
                orig_pos = int(pos * speed)
                orig_total = int(total * speed)
            else:
                orig_pos = pos
                orig_total = total

            # Tự động dừng khi hết bài
            if mode == "stopped" and not paused and total > 0 and pos >= total - 50:
                paused = True

            hist = (f"📚 Lịch sử: {self.history_idx + 1}/{len(self.history)}"
                    if len(self.history) > 1 else "")

            reset_cursor()
            print(render_player(preview, orig_pos, orig_total, speed, paused, hist))

            # Chờ input ~150ms (tốc độ làm mới UI)
            t0 = time.time()
            key = None
            while time.time() - t0 < 0.15:
                key = get_key()
                if key:
                    break
                time.sleep(0.02)

            if key == 'esc':
                self.mci.close()
                return

            elif key == 'space':
                if paused:
                    if mode == "stopped":
                        self.mci.play(0)
                    else:
                        self.mci.resume()
                    paused = False
                else:
                    self.mci.pause()
                    paused = True

            elif key == 'right':
                seek_delta = 5000 / speed if is_wav and abs(speed - 1.0) > 0.01 else 5000
                self.mci.seek(min(pos + seek_delta, total))
                if paused and mode != "stopped":
                    time.sleep(0.05)
                    self.mci.pause()

            elif key == 'left':
                seek_delta = 5000 / speed if is_wav and abs(speed - 1.0) > 0.01 else 5000
                self.mci.seek(max(0, pos - seek_delta))
                if paused and mode != "stopped":
                    time.sleep(0.05)
                    self.mci.pause()

            elif key == 'enter':
                self.mci.play(0)
                paused = False

            elif key == 'plus' and is_wav:
                idx = _nearest_speed_idx(speed)
                if idx < len(SPEEDS) - 1:
                    old_orig = int(pos * speed) if abs(speed - 1.0) > 0.01 else pos
                    speed = SPEEDS[idx + 1]
                    self.mci.close()
                    try:
                        current_file = create_speed_wav(audio_src, speed)
                    except Exception:
                        speed = 1.0
                        current_file = audio_src
                    self.mci.open(current_file)
                    self.mci.play(int(old_orig / speed))
                    if paused:
                        time.sleep(0.05)
                        self.mci.pause()

            elif key == 'minus' and is_wav:
                idx = _nearest_speed_idx(speed)
                if idx > 0:
                    old_orig = int(pos * speed) if abs(speed - 1.0) > 0.01 else pos
                    speed = SPEEDS[idx - 1]
                    self.mci.close()
                    try:
                        current_file = create_speed_wav(audio_src, speed)
                    except Exception:
                        speed = 1.0
                        current_file = audio_src
                    self.mci.open(current_file)
                    self.mci.play(int(old_orig / speed))
                    if paused:
                        time.sleep(0.05)
                        self.mci.pause()

            elif key == 'up' and len(self.history) > 1 and self.history_idx > 0:
                self.mci.close()
                self.history_idx -= 1
                item = self.history[self.history_idx]
                audio_src = item["audio_file"]
                preview = item["preview"]
                is_wav = audio_src.lower().endswith(".wav")
                speed = self.default_speed
                current_file = audio_src
                if is_wav and abs(speed - 1.0) > 0.01:
                    try:
                        current_file = create_speed_wav(audio_src, speed)
                    except Exception:
                        current_file = audio_src
                        speed = 1.0
                self.mci.open(current_file)
                self.mci.play()
                paused = False

            elif key == 'down' and len(self.history) > 1 and self.history_idx < len(self.history) - 1:
                self.mci.close()
                self.history_idx += 1
                item = self.history[self.history_idx]
                audio_src = item["audio_file"]
                preview = item["preview"]
                is_wav = audio_src.lower().endswith(".wav")
                speed = self.default_speed
                current_file = audio_src
                if is_wav and abs(speed - 1.0) > 0.01:
                    try:
                        current_file = create_speed_wav(audio_src, speed)
                    except Exception:
                        current_file = audio_src
                        speed = 1.0
                self.mci.open(current_file)
                self.mci.play()
                paused = False

    # ─── Settings Menu ───
    def settings_loop(self):
        selectable = [0, 1, 2, 3]   # engine, voice, speed, back
        si = 0

        clear()
        while True:
            sel = selectable[si]
            voices = KOKORO_VOICES if self.engine == "kokoro" else EDGE_VOICES
            reset_cursor()
            print(render_settings(sel, self.engine, self.voice, self.default_speed))

            key = wait_key()

            if key == 'up':
                si = (si - 1) % len(selectable)
            elif key == 'down':
                si = (si + 1) % len(selectable)

            elif key in ('left', 'right'):
                d = -1 if key == 'left' else 1
                if sel == 0:   # Engine
                    idx = ENGINES.index(self.engine) if self.engine in ENGINES else 0
                    self.engine = ENGINES[(idx + d) % len(ENGINES)]
                    voices = KOKORO_VOICES if self.engine == "kokoro" else EDGE_VOICES
                    self.voice = voices[0]
                elif sel == 1:  # Voice
                    idx = voices.index(self.voice) if self.voice in voices else 0
                    self.voice = voices[(idx + d) % len(voices)]
                elif sel == 2:  # Speed
                    idx = _nearest_speed_idx(self.default_speed)
                    self.default_speed = SPEEDS[(idx + d) % len(SPEEDS)]

            elif key == 'enter':
                if sel == 3:  # Back
                    self._save_config()
                    invalidate_local_engine()
                    self._server_on = check_server()
                    return
            elif key == 'esc':
                self._save_config()
                invalidate_local_engine()
                self._server_on = check_server()
                return


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        App().run()
    except KeyboardInterrupt:
        show_cursor()
        print(f"\n{C.GRAY}👋 Đã thoát.{C.RST}")
    except Exception as e:
        show_cursor()
        # Khôi phục lại screen buffer ban đầu để hiện lỗi
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()
        import traceback
        print(f"\n{C.RED}{C.BOLD}❌ ĐÃ XẢY RA LỖI HỆ THỐNG:{C.RST}")
        traceback.print_exc()
        print(f"\n{C.YELLOW}Vui lòng kiểm tra lỗi trên và báo lại với tui để tui sửa nhé!{C.RST}")
        input("\n⌨️ Nhấn Enter để đóng cửa sổ...")
