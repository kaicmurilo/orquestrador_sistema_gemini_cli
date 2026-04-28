import subprocess


def call_gemini(prompt: str, allow_modifications: bool = True, timeout: int = 120) -> str:
    cmd = ["gemini", "-p", prompt]
    if allow_modifications:
        cmd.append("--yolo")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gemini exited with non-zero status")

    output = result.stdout.strip()
    if not output:
        raise ValueError("gemini returned empty output")

    return output
