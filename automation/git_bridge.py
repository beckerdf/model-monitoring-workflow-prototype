"""
Git bridge: the Linux side's pull/push against the company repo, used to
exchange files with the Outlook VBA macros running on DB's Windows laptop.

Requires non-interactive git auth to already be set up (see
BRIDGE_SETUP.md) -- a GitHub Personal Access Token stored via
`git config credential.helper store`, done once by hand. Without that,
every pull/push here would hang waiting for a username/password that
will never come, since this runs unattended.
"""
import logging
import subprocess

from . import config

log = logging.getLogger("model_monitoring_workflow")


def _run_git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=config.BRIDGE_REPO_PATH,
        capture_output=True,
        text=True,
        timeout=60,
    )


def pull() -> bool:
    """Pull the latest from the company repo. Returns True on success."""
    result = _run_git("pull", "origin", "main", "--no-edit")
    if result.returncode != 0:
        log.error(f"git pull failed: {result.stderr.strip()}")
        return False
    return True


def push(message: str) -> bool:
    """Stage everything under bridge/, commit if there's anything to commit, and push."""
    _run_git("add", "bridge/")
    status = _run_git("status", "--porcelain", "bridge/")
    if not status.stdout.strip():
        return True  # nothing changed, nothing to push

    commit = _run_git("commit", "-m", message)
    if commit.returncode != 0:
        log.error(f"git commit failed: {commit.stderr.strip()}")
        return False

    result = _run_git("push", "origin", "main")
    if result.returncode != 0:
        log.error(f"git push failed: {result.stderr.strip()}")
        return False
    return True
