"""health_checker.py — Kiểm tra kết nối endpoint và health của model LLM cho Server"""

import requests
from openai import OpenAI
from src.config_manager import ConfigManager


def check_endpoint(api_base: str, timeout: int = 5) -> dict:
    result = {
        "status": "unknown",
        "latency_ms": None,
        "message": "",
    }

    if not api_base:
        result["status"] = "error"
        result["message"] = "⚠️ API Base URL đang trống"
        return result

    import time
    start = time.time()

    try:
        resp = requests.get(
            api_base,
            headers={"User-Agent": "WebToAudio/1.0"},
            timeout=timeout,
        )
        elapsed = round((time.time() - start) * 1000)
        result["latency_ms"] = elapsed

        if resp.status_code < 500:
            result["status"] = "ok"
            result["message"] = f"✅ Endpoint reachable ({elapsed}ms, HTTP {resp.status_code})"
        else:
            result["status"] = "error"
            result["message"] = f"❌ Endpoint trả về lỗi (HTTP {resp.status_code})"

    except requests.exceptions.ConnectionError:
        elapsed = round((time.time() - start) * 1000)
        result["latency_ms"] = elapsed
        result["status"] = "error"
        result["message"] = "❌ Không thể kết nối — kiểm tra URL hoặc network"

    except requests.exceptions.Timeout:
        result["status"] = "error"
        result["message"] = f"❌ Timeout sau {timeout}s"

    except Exception as e:
        result["status"] = "error"
        result["message"] = f"❌ Lỗi: {e}"

    return result


def check_model(config: ConfigManager) -> dict:
    result = {
        "status": "unknown",
        "latency_ms": None,
        "message": "",
        "response_preview": "",
    }

    api_key = config.get("api_key")
    api_base = config.get("api_base")
    model = config.get("model")

    if not api_key:
        result["status"] = "error"
        result["message"] = "⚠️ API Key đang trống"
        return result

    if not model:
        result["status"] = "error"
        result["message"] = "⚠️ Model name đang trống"
        return result

    import time
    start = time.time()

    try:
        client = OpenAI(api_key=api_key, base_url=api_base)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Chỉ trả lời 'ok'"}
            ],
            max_tokens=5,
            temperature=0.1,
        )

        elapsed = round((time.time() - start) * 1000)
        result["latency_ms"] = elapsed
        reply = resp.choices[0].message.content.strip() if resp.choices else ""
        result["response_preview"] = reply
        result["status"] = "ok"
        result["message"] = f"✅ Model '{model}' hoạt động ({elapsed}ms)"

    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        result["latency_ms"] = elapsed
        result["status"] = "error"
        result["message"] = f"❌ Model '{model}' lỗi: {e}"

    return result


def run_full_check(config: ConfigManager) -> dict:
    api_base = config.get("api_base")
    endpoint_result = check_endpoint(api_base)
    model_result = {"status": "skipped", "message": "⏭️ Bỏ qua — endpoint không khả dụng"}
    if endpoint_result["status"] == "ok":
        model_result = check_model(config)

    if endpoint_result["status"] == "ok" and model_result["status"] == "ok":
        overall = "✅ Mọi thứ hoạt động tốt!"
    elif endpoint_result["status"] == "ok" and model_result["status"] != "ok":
        overall = "⚠️ Endpoint OK nhưng model có vấn đề"
    else:
        overall = "❌ Có lỗi kết nối"

    return {
        "overall": overall,
        "endpoint": endpoint_result,
        "model": model_result,
    }
