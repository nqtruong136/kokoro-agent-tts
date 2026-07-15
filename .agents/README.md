# Antigravity Kokoro TTS Response Kit

Bộ này giúp Agent tạo một bản plain text dễ đọc bằng TTS từ câu trả lời chính, ghi ra file rồi gọi runner Kokoro của bạn.

## Thành phần

```text
.agents/
├── skills/
│   └── tts-response/
│       ├── SKILL.md
│       ├── references/
│       │   └── tts-format.md
│       └── scripts/
│           ├── invoke-tts.ps1
│           └── tts.config.psd1
├── rules/
│   └── tts-response-always-on.md
└── workflows/
    └── speak-response.md
```

## 1. Cài đặt

Copy thư mục `.agents` vào root project.

## 2. Cấu hình Kokoro runner

Mở:

```text
.agents/skills/tts-response/scripts/tts.config.psd1
```

Sửa ba phần:

```powershell
RunnerPath = 'G:\kokoro\run-tts.bat'
WorkingDirectory = 'G:\kokoro'
Arguments = @('--input-file', '{input}')
```

Nếu runner nhận input như sau:

```powershell
.\speak.ps1 -InputTextFile "path\response.txt"
```

thì cấu hình:

```powershell
RunnerPath = 'G:\kokoro\speak.ps1'
Arguments = @('-InputTextFile', '{input}')
```

Nếu runner chỉ nhận file ở tham số thứ nhất:

```powershell
Arguments = @('{input}')
```

## 3. Test thủ công

Từ root project:

```powershell
New-Item -ItemType Directory -Force ".agent-output\tts" | Out-Null
Set-Content -LiteralPath ".agent-output\tts\latest-response.txt" -Encoding utf8 -Value "Xin chào. Đây là bài kiểm tra Kokoro TTS."

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File ".agents\skills\tts-response\scripts\invoke-tts.ps1" `
  -InputFile ".agent-output\tts\latest-response.txt"
```

## 4. Bật cho mọi câu trả lời

Mở Customizations → Rules, chọn rule `tts-response-always-on` và đặt activation thành **Always On**.

Skill tự nó được nạp theo mức độ liên quan. Rule Always On là phần buộc Agent chạy TTS ở cuối mọi phản hồi.

## 5. Chỉ dùng khi cần

Không bật Always On. Gọi:

```text
/speak-response
```

để đọc lại câu trả lời gần nhất.

Hoặc thêm skill vào workflow:

```markdown
## Skills bắt buộc

- `backend-engineering`
- `qa-testing`
- `tts-response`

## Finalize response

Trước khi gửi câu trả lời chính, thực hiện skill `tts-response`.
```

## File đầu vào TTS

Mặc định:

```text
.agent-output/tts/latest-response.txt
```

File này bị ghi đè sau mỗi phản hồi. Thêm `.agent-output/` vào `.gitignore` nếu không muốn commit.

## Lưu ý về quyền

Antigravity có thể hỏi xác nhận khi Agent chạy PowerShell hoặc runner bên ngoài workspace. Chỉ allowlist đúng script/path bạn tin tưởng. Không cần chuyển toàn bộ Agent sang chế độ bỏ qua kiểm tra.

## Hạn chế thực tế

Skill không phải một UI post-response hook. Agent phải chuẩn bị file và gọi TTS ngay trước khi gửi final response. Nếu cần bảo đảm tuyệt đối ở cấp ứng dụng, nên dùng lifecycle hook hoặc MCP/tool riêng thay vì chỉ dựa vào prompt.
