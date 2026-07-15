# 🎙️ Web-to-Audio Quick TTS Player (Offline Portable Release)

Bộ công cụ phát âm thanh văn bản (TTS) tiếng Việt ngoại tuyến (Offline), hỗ trợ giao diện trình phát TUI (Terminal User Interface) hiện đại phong cách Gemini/Claude CLI, cùng khả năng tích hợp làm công cụ đọc phản hồi cho các AI Agent (như trợ lý ảo Antigravity).

Bản phân phối này tách biệt rõ ràng pha thiết lập (`setup.bat`) và pha khởi chạy (`run.bat` / `clip_tts.bat` / `agent_tts.bat`) để mang lại trải nghiệm tối ưu nhất cho người dùng cuối và các nhà phát triển.

---

## 📁 Cấu trúc thư mục

```text
tts_release/
├── .agents/            # Thư mục cấu hình tích hợp trợ lý ảo AI Agent (nếu dùng)
├── uv.exe              # Trình quản lý môi trường chạy siêu tốc của Astral (chỉ ~8MB)
├── pyproject.toml      # Khai báo các gói thư viện phụ thuộc (PyTorch, Kokoro...)
├── uv.lock             # File khóa phiên bản thư viện đảm bảo chạy ổn định
├── model/              # Model Kokoro 82M & các giọng đọc tiếng Việt offline
├── src/                # Module xử lý lõi âm thanh
├── voicepacks/         # Thư mục chứa giọng đọc custom (.bin)
├── output/             # Thư mục xuất file âm thanh tạm thời
├── config.json         # File cấu hình hoạt động ngoại tuyến
├── clip_tts.py         # Mã nguồn chính chạy giao diện TUI và xử lý phát âm thanh
├── setup.bat           # [1] Click đúp để tự động cài đặt thư viện khi tải về lần đầu
├── run.bat             # [2] Click đúp để khởi chạy ứng dụng TUI Player (Đọc Clipboard)
├── clip_tts.bat        # [2] (Tương tự run.bat) Khởi chạy ứng dụng TUI Player
├── agent_tts.bat       # [3] Chạy âm thanh chế độ phi tương tác (Tự động đóng khi phát xong)
└── README.md           # Hướng dẫn này
```

---

## 🚀 Hướng dẫn sử dụng cho Người Dùng Cuối

Chỉ cần giải nén thư mục `tts_release` ra bất kỳ phân vùng ổ đĩa nào và làm theo 2 bước đơn giản:

### Bước 1: Thiết lập môi trường (Chỉ chạy duy nhất LẦN ĐẦU TIÊN)
* Click đúp chuột vào file **`setup.bat`**.
* Chương trình sẽ tự động dùng công cụ `uv.exe` để tạo môi trường chạy ảo `.venv` cô lập và tải các gói thư viện cần thiết (PyTorch CUDA, Kokoro TTS...). Quá trình này diễn ra hoàn toàn tự động và mất khoảng 1-2 phút tùy tốc độ mạng.
* Sau khi có thông báo hoàn tất thành công, bạn có thể đóng cửa sổ lại.

### Bước 2: Khởi chạy ứng dụng
* Click đúp chuột vào file **`run.bat`** hoặc **`clip_tts.bat`** để mở ứng dụng tức thì (khởi động cực nhanh trong **0.5 giây**).

---

## 🎮 Điều khiển trình phát TUI (Menu TUI)

Khi mở ứng dụng bằng `run.bat`:
* Chọn dòng số **1 (📋 Đọc Clipboard & Phát Audio)** để đọc văn bản đang có sẵn trong Clipboard của bạn.
* Trình phát âm thanh TUI hỗ trợ các phím điều khiển nhanh trực tiếp từ bàn phím:
  * `[Space]`: Tạm dừng / Tiếp tục phát âm thanh.
  * `[← / →]`: Tua nhanh / Tua lại ±5 giây.
  * `[+ / -]`: Tăng / Giảm tốc độ đọc (Chỉ áp dụng với chế độ phát offline).
  * `[↑ / ↓]`: Xem lại lịch sử hoặc chuyển bài trước/sau.
  * `[Enter]`: Phát lại từ đầu.
  * `[Esc]`: Thoát về Menu chính.

### Đọc trực tiếp từ tham số dòng lệnh hoặc file:
* **Đọc chuỗi văn bản trực tiếp**: `run.bat "Nội dung văn bản muốn phát âm thanh"`
* **Đọc từ file văn bản (.txt)**: `run.bat "đường_dẫn_đến_file_chữ.txt"` (tự động đọc nội dung chữ bên trong file).

---

## ⚙️ Cấu hình Tùy chỉnh (`config.json`)

Bạn có thể chỉnh sửa file `config.json` trực tiếp bằng Notepad để thay đổi hành vi:
* `"kokoro_device": "cuda"`: Chạy sinh giọng đọc bằng GPU (Nvidia CUDA) để đạt hiệu suất siêu tốc (gần như tức thì). Nếu máy không hỗ trợ card rời Nvidia, hãy đổi thành `"cpu"`.
* `"kokoro_voice": "hung_thinh"`: Đổi giọng mặc định. Các giọng đọc ngoại tuyến được hỗ trợ bao gồm:
  * `hung_thinh` (Giọng nam miền Nam)
  * `thanh_dat` (Giọng nam miền Bắc)
  * `manh_dung` (Giọng nam)
  * `ngoc_huyen` (Giọng nữ)
  * `tuan_ngoc` (Giọng nam)
  * `custom_voice` (Giọng tùy biến nằm trong thư mục `voicepacks/`)

---

## 🤖 Hướng dẫn tích hợp AI Agent (Dành cho Lập Trình Viên)

Bộ công cụ này đi kèm tệp **`agent_tts.bat`** chuyên dụng cho việc tích hợp tự động hóa vào các AI Agent (như Antigravity).

### 1. Đặc điểm của `agent_tts.bat` (Chế độ phi tương tác):
* Không vẽ giao diện TUI, không chiếm dụng bộ nhớ đệm màn hình.
* Tự động nhận diện file input hoặc chuỗi văn bản truyền vào qua tham số dòng lệnh hoặc cờ `--input-file`.
* **Tự động đóng cửa sổ CMD** ngay lập tức sau khi phát xong âm thanh để giải phóng màn hình.

### 2. Cấu hình tích hợp di động (Portable `.agents`):
Nếu bạn muốn đóng gói và mang thư mục `.agents` này sang máy khác chạy, hãy cấu hình file `.agents\skills\tts-response\scripts\tts.config.psd1` của Agent bằng **đường dẫn tương đối** như sau:

```powershell
@{
    # Bật/Tắt trình phát của Agent
    Enabled = $true

    # Đường dẫn tương đối trỏ tới file agent_tts.bat
    RunnerPath = '.\agent_tts.bat'

    # Để chuỗi rỗng để tự động nhận diện thư mục làm việc theo vị trí file bat
    WorkingDirectory = ''

    # Tham số truyền vào cho file bat
    Arguments = @('--input-file', '{input}')

    # Chạy nền không chặn luồng suy nghĩ của Agent
    RunInBackground = $true

    # Phải đặt là $false vì ứng dụng TUI cần cửa sổ console để Win32 MCI khởi tạo âm thanh
    HiddenWindow = $false
}
```

*Lưu ý*: Với cấu hình tương đối ở trên, khi người dùng mở thư mục chứa bản release này bằng VS Code/Cursor làm thư mục gốc (Workspace), AI Agent của họ sẽ tự động gọi được trình phát phát âm thanh mà không cần cấu hình lại thủ công.


---

## 📄 Bản quyền & Ghi công (License & Attribution)

### 1. Giấy phép sử dụng (License)
Dự án này được phát hành dưới giấy phép **[CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/)** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International).
* **Phi thương mại (Non-Commercial):** Nghiêm cấm mọi hành vi sử dụng mã nguồn, kịch bản đóng gói (`.bat`) hoặc bộ Voicepacks đi kèm trong dự án này vào mục đích thương mại trực tiếp hoặc gián tiếp khi chưa có sự đồng ý bằng văn bản của tác giả.
* **Ghi nguồn (Attribution):** Mọi bản phân phối lại hoặc phát triển dựa trên dự án này phải ghi rõ nguồn dẫn về repository gốc: [nqtruong136/kokoro-agent-tts](https://github.com/nqtruong136/kokoro-agent-tts).

### 2. Ghi công mô hình gốc & Bản Việt hóa (Model Attribution)
Trình phát này tích hợp và sử dụng sức mạnh của mô hình chuyển đổi văn bản thành giọng nói tiếng Việt chất lượng cao, được xây dựng từ hai nguồn đóng góp vĩ đại:
* **Mô hình gốc Kokoro-82M:**
  * **Tác giả:** @hexgrad
  * **Đặc điểm:** Mô hình TTS mã nguồn mở siêu nhẹ (82 triệu tham số) nhưng đạt chất lượng tương đương các giải pháp thương mại lớn.
  * **Giấy phép:** Apache-2.0 License.
* **Bản Việt hóa Kokoro-Vietnamese:**
  * **Tác giả:** @iamdinhthuan (Đinh Thuận)
  * **Đặc điểm:** Tinh chỉnh (fine-tuned) trên tập dữ liệu tiếng Việt chất lượng cao **LarVoice**, giúp tạo ra các giọng đọc nam/nữ của cả hai miền Nam và Bắc cực kỳ truyền cảm, tự nhiên.
  * **Giấy phép:** Kế thừa giấy phép Apache-2.0.

Chúng tôi xin bày tỏ lòng biết ơn sâu sắc tới `@hexgrad` vì nền tảng mô hình vượt trội và `@iamdinhthuan` vì những nỗ lực tuyệt vời trong việc mang lại giọng đọc tiếng Việt tự nhiên cho cộng đồng!

