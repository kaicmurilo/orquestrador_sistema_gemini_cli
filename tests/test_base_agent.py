import subprocess
import pytest
from unittest.mock import patch, MagicMock
from agents.base_agent import call_gemini


def test_call_gemini_returns_stdout():
    mock_result = MagicMock()
    mock_result.stdout = "  gemini output  "
    mock_result.returncode = 0

    with patch("agents.base_agent.subprocess.run", return_value=mock_result) as mock_run:
        result = call_gemini("test prompt")
        assert result == "gemini output"
        mock_run.assert_called_once_with(
            ["gemini", "-p", "test prompt", "--yolo"],
            capture_output=True, text=True, timeout=120
        )


def test_call_gemini_without_modifications():
    mock_result = MagicMock()
    mock_result.stdout = "output"
    mock_result.returncode = 0

    with patch("agents.base_agent.subprocess.run", return_value=mock_result) as mock_run:
        call_gemini("prompt", allow_modifications=False)
        cmd = mock_run.call_args[0][0]
        assert "--yolo" not in cmd


def test_call_gemini_raises_on_empty_output():
    mock_result = MagicMock()
    mock_result.stdout = "   "
    mock_result.returncode = 0

    with patch("agents.base_agent.subprocess.run", return_value=mock_result):
        with pytest.raises(ValueError, match="empty output"):
            call_gemini("prompt")


def test_call_gemini_raises_on_nonzero_returncode():
    mock_result = MagicMock()
    mock_result.stdout = "some output"
    mock_result.returncode = 1
    mock_result.stderr = "gemini error"

    with patch("agents.base_agent.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="gemini error"):
            call_gemini("prompt")


def test_call_gemini_raises_on_timeout():
    with patch("agents.base_agent.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="gemini", timeout=120)):
        with pytest.raises(RuntimeError, match="timed out"):
            call_gemini("prompt")
