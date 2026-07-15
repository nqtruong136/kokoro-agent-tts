---
name: tts-response
description: Tạo phiên bản plain text tự nhiên dành cho Text-to-Speech từ câu trả lời cuối của Agent, ghi UTF-8 vào file và gọi Kokoro TTS runner đã cấu hình. Dùng khi người dùng muốn Agent đọc câu trả lời, khi workflow khai báo tts-response, hoặc khi TTS Always On Rule đang bật.
---

# TTS Response

## Mục tiêu

Với mỗi câu trả lời chính dành cho người dùng:

1. Soạn nội dung trả lời hiển thị bình thường.
2. Tạo một phiên bản riêng tối ưu cho TTS.
3. Ghi phiên bản TTS vào file UTF-8.
4. Gọi script Kokoro TTS đã cấu hình.
5. Sau đó mới gửi câu trả lời hiển thị cho người dùng.

Đây là bước finalization của phản hồi, không phải nội dung thay thế câu trả lời chính.

## Thứ tự bắt buộc

Thực hiện theo đúng thứ tự:

1. Hoàn thiện nội dung user-facing response.
2. Chuyển nội dung đó thành `spoken response` theo quy tắc bên dưới.
3. Tạo thư mục `.agent-output/tts/` nếu chưa tồn tại.
4. Ghi `spoken response` vào:

   `.agent-output/tts/latest-response.txt`

5. File phải là plain text UTF-8, không chứa Markdown.
6. Gọi:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".agents\skills\tts-response\scripts\invoke-tts.ps1" -InputFile ".agent-output\tts\latest-response.txt"
   ```

7. Nếu TTS chạy thành công, gửi câu trả lời chính.
8. Nếu TTS lỗi, vẫn gửi câu trả lời chính và thêm một ghi chú ngắn về lỗi; không che giấu lỗi.
9. Không gọi TTS lặp lại cho cùng một phản hồi.

## Quy tắc tạo spoken response

Spoken response phải giữ đúng ý nghĩa của câu trả lời chính nhưng được viết để nghe tự nhiên.

### Bắt buộc

- Dùng câu hoàn chỉnh và dấu câu tạo nhịp nghỉ tự nhiên.
- Bỏ ký hiệu Markdown như `#`, `**`, backtick và dấu gạch đầu dòng.
- Chuyển danh sách thành “Thứ nhất”, “Thứ hai” hoặc các câu nối tự nhiên.
- Với tiêu đề, đọc như một câu dẫn ngắn.
- Giữ nguyên cảnh báo, kết luận và thông tin quan trọng.
- Mở rộng chữ viết tắt khi chắc chắn về nghĩa; nếu không chắc, giữ nguyên.
- Mô hình TTS được tích hợp thư viện chuẩn hóa `sea-g2p` có khả năng đọc song ngữ Anh-Việt rất tốt. Do đó, đối với các thuật ngữ tiếng Anh kỹ thuật phổ biến (như API, SQL, JSON, Git, Docker, Python, CUDA, UI, AI...), hãy giữ nguyên từ gốc tiếng Anh thay vì viết phiên âm tiếng Việt (như a-p-i, cu-đa...), công cụ G2P sẽ tự động xử lý phát âm chuẩn xác.
- Với số liệu quan trọng, giữ đủ giá trị và đơn vị.
- Không thêm nhận định mới không có trong câu trả lời chính.
- Không đọc citation marker, metadata, ID nội bộ hoặc đường dẫn tải xuống dạng sandbox.

### Code và câu lệnh

- Không đọc từng ký tự của code block dài.
- Tóm tắt mục đích của code bằng ngôn ngữ tự nhiên.
- Chỉ đọc câu lệnh ngắn nếu nó cần thiết để người nghe thao tác.
- Với đường dẫn file quan trọng, đọc tên file hoặc đường dẫn ở mức vừa đủ; tránh đọc từng dấu gạch khi không cần.
- Không đọc raw JSON, stack trace, hash, token hoặc nội dung máy khó nghe.

### Link và bảng

- Đọc tên tài liệu hoặc nội dung link, không đọc URL dài.
- Chuyển bảng thành các câu so sánh ngắn.
- Không đọc Markdown table separator.

### Dữ liệu nhạy cảm

Không ghi hoặc đọc:

- Password.
- API key.
- Access token.
- Secret.
- Cookie/session.
- Private key.
- Dữ liệu cá nhân không cần thiết.

Nếu câu trả lời chứa dữ liệu nhạy cảm, loại phần nhạy cảm khỏi spoken response và nói rằng phần đó được bỏ qua vì an toàn.

## Phạm vi

Chỉ đọc câu trả lời chính dành cho người dùng.

Không đưa vào spoken response:

- Chain of thought.
- Scratchpad.
- Lệnh terminal nội bộ.
- Log tool dài.
- Nội dung file được đọc trong quá trình làm việc, trừ phần đã xuất hiện trong câu trả lời chính.
- Thông báo tiến độ tạm thời.

## Trường hợp bỏ qua

Bỏ qua TTS khi:

- Người dùng nói rõ không đọc phản hồi đó.
- Không có câu trả lời user-facing, chỉ đang chờ người dùng cung cấp dữ liệu.
- Runner chưa được cấu hình.
- Việc thực thi bị từ chối bởi permission hoặc sandbox.

Khi bỏ qua do lỗi cấu hình hoặc quyền, báo ngắn gọn và nêu file/script cần kiểm tra.

## Kiểm tra trước khi gửi

- Spoken response có cùng kết luận với câu trả lời chính.
- Không còn Markdown khó đọc.
- Không chứa secret hoặc dữ liệu nội bộ.
- File `latest-response.txt` đã được ghi thành công.
- Runner chỉ được gọi một lần.
