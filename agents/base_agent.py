import subprocess


def call_gemini(prompt: str, allow_modifications: bool = True, timeout: int = 120) -> str:
    cmd = ["gemini", "-p", prompt]
    if allow_modifications:
        cmd.append("--yolo")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"gemini timed out after {timeout}s")

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gemini exited with non-zero status")

    output = result.stdout.strip()
    if not output:
        raise ValueError("gemini returned empty output")

    return output
