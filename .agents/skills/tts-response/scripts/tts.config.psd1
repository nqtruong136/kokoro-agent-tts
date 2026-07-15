@{
    # Bật hoặc tắt runner.
    Enabled = $true

    # ĐỔI đường dẫn dưới đây thành file .bat, .cmd, .ps1 hoặc .exe của dự án Kokoro.
    RunnerPath = 'G:\03_BAITAP\my-browser-agent\tools\web-to-audio-server\agent_tts.bat'

    # Có thể để trống; khi để trống sẽ dùng thư mục chứa RunnerPath.
    WorkingDirectory = 'G:\03_BAITAP\my-browser-agent\tools\web-to-audio-server'

    # {input} sẽ được thay bằng đường dẫn tuyệt đối của latest-response.txt.
    # Ví dụ runner của bạn dùng: run-tts.bat --input-file <path>
    Arguments = @('--input-file', '{input}')

    # $true: khởi chạy TTS nền để Agent không phải đợi đọc xong.
    # $false: đợi runner kết thúc và nhận exit code đáng tin cậy hơn.
    RunInBackground = $true

    # Chỉ áp dụng khi RunInBackground = $true.
    HiddenWindow = $true
}
