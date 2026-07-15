---
description: "Đọc lại câu trả lời gần nhất bằng Kokoro TTS"
---

# Speak Last Response

## Skill bắt buộc

Nạp và đọc đầy đủ skill:

- `tts-response`

Nếu không tìm thấy, báo:

`Missing skill: tts-response`

## Các bước

1. Lấy câu trả lời user-facing hoàn chỉnh gần nhất của Agent trong conversation.
2. Không lấy progress update, tool output hoặc nội dung nội bộ.
3. Tạo spoken response theo skill `tts-response`.
4. Ghi UTF-8 vào `.agent-output/tts/latest-response.txt`.
5. Gọi runner bằng script `invoke-tts.ps1`.
6. Báo ngắn gọn TTS đã được khởi chạy hoặc nêu lỗi thực tế.
