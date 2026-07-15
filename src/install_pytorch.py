"""install_pytorch.py — Tự động phát hiện GPU NVIDIA và cài đặt bản PyTorch CUDA phù hợp hoặc CPU cho Server"""

import subprocess
import sys
import re
import os


def get_nvidia_driver_version():
    """Kiểm tra Driver NVIDIA và trả về phiên bản CUDA tương thích tối đa"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        driver_version_str = result.stdout.strip()
        driver_version = float(re.findall(r"^\d+\.\d+", driver_version_str)[0])
        
        print(f"🔍 Phát hiện GPU NVIDIA (Phiên bản Driver: {driver_version_str})")
        
        if driver_version >= 525.60:
            return "cu124"
        elif driver_version >= 511.23:
            return "cu121"
        elif driver_version >= 452.39:
            return "cu118"
        else:
            return "cpu"
            
    except (subprocess.SubprocessError, FileNotFoundError, IndexError, ValueError):
        print("ℹ️ Không phát hiện GPU NVIDIA hoặc Driver chưa cài đặt. Sử dụng CPU.")
        return "cpu"


def check_torch_installed_with_cuda(required_cuda):
    """Kiểm tra xem PyTorch hiện tại đã được cài đúng bản CUDA cần thiết chưa"""
    try:
        import torch
        version = torch.__version__
        cuda_available = torch.cuda.is_available()
        
        if required_cuda == "cpu":
            if "+cpu" in version or not cuda_available:
                print("✅ PyTorch CPU đã được cài đặt chính xác.")
                return True
            else:
                print("⚠️ PyTorch hiện tại là bản CUDA nhưng hệ thống yêu cầu bản CPU.")
                return False
        else:
            if cuda_available and required_cuda in version:
                print(f"✅ PyTorch {version} đã được cài đặt chính xác với CUDA ({required_cuda}).")
                return True
            elif cuda_available:
                print(f"ℹ️ PyTorch đã cài đặt với CUDA (Version: {version}), sẵn sàng sử dụng.")
                return True
            else:
                print(f"⚠️ PyTorch hiện tại là bản CPU ({version}) nhưng máy có hỗ trợ GPU CUDA.")
                return False
    except ImportError:
        print("ℹ️ PyTorch chưa được cài đặt.")
        return False


def install_pytorch():
    cuda_ver = get_nvidia_driver_version()
    
    if check_torch_installed_with_cuda(cuda_ver):
        print("🚀 PyTorch đã sẵn sàng, bỏ qua bước cài đặt.")
        return

    if cuda_ver == "cpu":
        print("📥 Đang tải và cài đặt PyTorch (phiên bản CPU)...")
        cmd = ["uv", "pip", "install", "torch", "torchvision", "torchaudio"]
    else:
        print(f"📥 Đang tải và cài đặt PyTorch tương thích CUDA {cuda_ver[-2:]}.x ({cuda_ver})...")
        index_url = f"https://download.pytorch.org/whl/{cuda_ver}"
        cmd = [
            "uv", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", index_url,
            "--force-reinstall"
        ]
        
    try:
        subprocess.run(cmd, check=True)
        print("✅ Cài đặt PyTorch thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi trong quá trình cài đặt: {e}")
        sys.exit(1)


if __name__ == "__main__":
    install_pytorch()
