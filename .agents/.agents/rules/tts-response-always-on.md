---
trigger: always_on
---

# Antigravity Workspace Rules

## Rule: TTS Response Always On

Áp dụng rule này cho mọi câu trả lời chính dành cho người dùng.

Trước khi gửi final response:

1. Nạp skill `tts-response`.
2. Thực hiện đầy đủ bước finalization trong skill.
3. Tạo spoken response từ đúng nội dung user-facing response.
4. Ghi `.agent-output/tts/latest-response.txt`.
5. Chạy Kokoro TTS runner.
6. Chỉ sau đó mới gửi final response.

Không áp dụng cho progress update, tool log hoặc chain of thought.

Nếu người dùng nói “không đọc”, “tắt TTS” hoặc ý tương đương, bỏ qua TTS cho phản hồi đó.

Nếu runner lỗi, vẫn gửi câu trả lời chính và báo lỗi TTS bằng một câu ngắn. Không để lỗi TTS làm mất nội dung trả lời.
