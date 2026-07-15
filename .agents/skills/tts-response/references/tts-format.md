# TTS Formatting Reference

## Ví dụ 1: Markdown kỹ thuật

Bản hiển thị:

```markdown
## Kết quả

- API đã chạy.
- Test: 18/18 passed.
- File sửa: `src/order.ts`.
```

Bản TTS:

```text
Kết quả như sau. API đã chạy thành công. Cả mười tám bài kiểm thử đều đã vượt qua. File được chỉnh sửa là src order chấm t s.
```

## Ví dụ 2: Code dài

Bản hiển thị chứa một code block nhiều dòng.

Bản TTS không đọc nguyên code. Dùng dạng:

```text
Tôi đã cung cấp đoạn mã cấu hình ở phần hiển thị. Đoạn mã này nhận đường dẫn file đầu vào, kiểm tra file tồn tại, sau đó gọi Kokoro TTS.
```

## Ví dụ 3: Cảnh báo

Bản hiển thị:

```markdown
> Cảnh báo: migration này có thể khóa bảng.
```

Bản TTS:

```text
Cảnh báo quan trọng. Migration này có thể khóa bảng.
```

## Ví dụ 4: Link

Bản hiển thị:

```markdown
Xem [tài liệu Agent Skills](...).
```

Bản TTS:

```text
Bạn có thể xem tài liệu Agent Skills để biết thêm chi tiết.
```

## Phát âm nội dung kỹ thuật

Không cố tự phiên âm mọi tên công nghệ. Giữ tên phổ biến như API, SQL, JSON, Git, Docker hoặc Kokoro nếu engine đọc ổn. Chỉ mở rộng từ viết tắt khi điều đó giúp dễ hiểu và không làm sai nghĩa.
