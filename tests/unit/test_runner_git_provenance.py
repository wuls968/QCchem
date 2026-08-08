from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from qcchem.workflow import runner


def test_git_stdout_uses_dash_c_without_cwd(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(stdout="abc123\n")

    monkeypatch.setattr(runner.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner._git_stdout(tmp_path, ["rev-parse", "HEAD"]) == "abc123"

    assert captured["cmd"] == ["/usr/bin/git", "-C", str(tmp_path), "rev-parse", "HEAD"]
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert "cwd" not in kwargs
    assert kwargs["stdin"] == runner.subprocess.DEVNULL
    assert kwargs["close_fds"] is False
    assert kwargs["timeout"] == runner.GIT_COMMAND_TIMEOUT_SECONDS


def test_git_provenance_snapshot_reuses_one_status_call(monkeypatch, tmp_path: Path) -> None:
    runner._git_provenance_snapshot.cache_clear()
    calls: list[tuple[str, ...]] = []

    def fake_git_stdout(root: Path, args: list[str], *, strip: bool = True):
        calls.append(tuple(args))
        if args == ["rev-parse", "HEAD"]:
            return "1234567890abcdef"
        if args == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return "codex/test"
        if args == ["describe", "--always", "--dirty", "--tags"]:
            return "1234567-dirty"
        if args == ["remote", "get-url", "origin"]:
            return "https://example.test/qcchem.git"
        if args == ["status", "--porcelain"]:
            return " M README.md\nA  staged.py\n?? scratch.txt\n"
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(runner, "_git_stdout", fake_git_stdout)

    first = runner._git_provenance_snapshot(tmp_path)
    second = runner._git_provenance_snapshot(tmp_path)

    assert first is second
    assert calls.count(("status", "--porcelain")) == 1
    assert len(calls) == 5
    assert first.commit == "1234567890abcdef"
    assert first.branch == "codex/test"
    assert first.describe == "1234567-dirty"
    assert first.remote_origin == "https://example.test/qcchem.git"
    assert first.workspace_dirty is True
    assert first.status_summary == {"staged": 1, "unstaged": 1, "untracked": 1}

    runner._git_provenance_snapshot.cache_clear()
