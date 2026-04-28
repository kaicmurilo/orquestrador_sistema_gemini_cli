import json
import subprocess


def call_gemini(prompt: str, allow_modifications: bool = True, timeout: int = 120) -> str:
    cmd = ["gemini", "-p", prompt, "--output-format", "json"]
    if allow_modifications:
        cmd.append("--yolo")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"gemini timed out after {timeout}s")

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gemini exited with non-zero status")

    raw = result.stdout.strip()
    if not raw:
        raise ValueError("gemini returned empty output")

    try:
        # extract only the JSON object (hook output may appear after it)
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(raw)
        output = data.get("response", "").strip()
    except (json.JSONDecodeError, AttributeError):
        output = raw

    if not output:
        raise ValueError("gemini returned empty output")

    return output
