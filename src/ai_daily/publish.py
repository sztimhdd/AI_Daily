"""Publishing: durable repo write + verified remote push, or local-only.

The publisher writes the final article plus recovery files (package
metadata, sources, cover if present) into a publish repo, pushes to the
remote when reachable, and then RE-READS the remote content to hash it
— the recorded SHA proves what the remote actually serves, not what we
intended to send.

When the remote is unavailable or the re-read hash mismatches, the
result is explicitly ``mode="local-only"``: the recovery commit still
exists in the publish repo, but no remote success is claimed.  Fake
success is forbidden.

Credentials are never automated.  The Git transport uses whatever
ambient authentication the editor's machine already has; the pipeline
never stores, prompts for, or fabricates credentials.
"""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import subprocess

from . import state, topics

PUBLISH_MESSAGE_PREFIX = "publish"


class PublishError(RuntimeError):
    """Raised when publishing cannot even start (missing assembled article)."""


@dataclasses.dataclass
class PublishResult:
    ok: bool
    mode: str            # "remote" | "local-only"
    reason: str = ""
    remote_sha256: str = ""
    local_sha256: str = ""
    published_relpath: str = ""


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------


class GitTransport:
    """Real git transport: commit locally, push, fetch, re-read.

    ``repo_dir`` is created/initialized on demand.  A remote is only
    configured when ``remote_url`` is given; an unreachable remote makes
    ``available()`` return False instead of raising.
    """

    def __init__(self, repo_dir, remote_url=None, remote="origin", branch="main"):
        self.repo_dir = pathlib.Path(repo_dir)
        self.remote_url = remote_url
        self.remote = remote
        self.branch = branch

    # -- repo preparation -------------------------------------------------
    def _git(self, *args, check=True):
        return subprocess.run(
            ["git", *args], cwd=str(self.repo_dir), capture_output=True, text=True,
            check=check,
        )

    def ensure_repo(self) -> None:
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        if not (self.repo_dir / ".git").exists():
            init = self._git("init", "-b", self.branch, check=False)
            if init.returncode != 0:  # very old git without -b
                self._git("init")
                self._git("symbolic-ref", "HEAD", f"refs/heads/{self.branch}")
        if self.remote_url:
            remotes = self._git("remote").stdout.split()
            if self.remote not in remotes:
                self._git("remote", "add", self.remote, self.remote_url)

    # -- transport interface ----------------------------------------------
    def available(self) -> bool:
        """True when the remote exists and answers ls-remote."""
        try:
            self.ensure_repo()
            remotes = self._git("remote", check=False).stdout.split()
            if self.remote not in remotes:
                return False
            probe = self._git("ls-remote", self.remote, "HEAD", check=False)
            return probe.returncode == 0
        except OSError:
            return False

    def push(self, files: dict) -> None:
        """Commit the (already written) payload and push.  Raises on failure."""
        self.ensure_repo()
        self._git("add", "-A")
        staged = self._git("diff", "--cached", "--name-only").stdout.strip()
        if staged:
            self._git(
                "-c", "user.name=AI Daily",
                "-c", "user.email=ai-daily@localhost",
                "commit", "-m", f"{PUBLISH_MESSAGE_PREFIX}: {len(files)} file(s)",
            )
        push = self._git("push", self.remote, f"HEAD:{self.branch}", check=False)
        if push.returncode != 0:
            raise RuntimeError(
                f"push failed: {(push.stderr or push.stdout).strip()[:300]}"
            )

    def read_remote(self, relpath: str) -> bytes:
        """Re-read a file from the remote after push (via fetch)."""
        fetch = self._git("fetch", self.remote, self.branch, check=False)
        if fetch.returncode != 0:
            raise RuntimeError(f"fetch failed: {(fetch.stderr or '').strip()[:300]}")
        show = self._git("show", f"FETCH_HEAD:{relpath}", check=False)
        if show.returncode != 0:
            raise RuntimeError(f"remote re-read failed for {relpath}")
        return show.stdout.encode("utf-8") if isinstance(show.stdout, str) else show.stdout


# ---------------------------------------------------------------------------
# Payload assembly
# ---------------------------------------------------------------------------


def _payload_files(run_paths, slug: str) -> dict:
    """Article + recovery files as {relpath: bytes}."""
    root = run_paths.root
    final = run_paths.final_article_path(slug)
    package = run_paths.package_dir(slug)
    if not final.is_file():
        raise PublishError(f"no assembled article at {final}; run assemble first")
    files = {str(final.relative_to(root)): final.read_bytes()}
    for name in ("article.md", "metadata.json", "sources.md"):
        path = package / name
        if path.is_file():
            files[str(path.relative_to(root))] = path.read_bytes()
    images = package / "images"
    if images.is_dir():
        for img in sorted(images.iterdir()):
            if img.is_file():
                files[str(img.relative_to(root))] = img.read_bytes()
    return files


# ---------------------------------------------------------------------------
# Publish entry point
# ---------------------------------------------------------------------------


def publish(run_paths, repo_dir, transport=None, **transport_kwargs) -> PublishResult:
    """Publish with verified remote write, or explicit local-only fallback."""
    topic = topics.require_choice(run_paths)
    slug = topic["slug"]
    files = _payload_files(run_paths, slug)
    article_rel = str(run_paths.final_article_path(slug).relative_to(run_paths.root))
    local_sha = hashlib.sha256(files[article_rel]).hexdigest()

    if transport is None:
        transport = GitTransport(repo_dir, **transport_kwargs)

    result = PublishResult(ok=True, mode="local-only", published_relpath=article_rel)
    result.local_sha256 = local_sha

    # Durable recovery copy first: the payload is always written into the
    # publish repo before any remote interaction, regardless of transport.
    repo_root = pathlib.Path(repo_dir)
    for rel, data in files.items():
        dest = repo_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    remote_ok = False
    try:
        if transport.available():
            transport.push(files)
            remote_bytes = transport.read_remote(article_rel)
            remote_sha = hashlib.sha256(remote_bytes).hexdigest()
            if remote_sha == local_sha:
                result.mode = "remote"
                result.remote_sha256 = remote_sha
                result.reason = "remote publish verified by re-read hash"
                remote_ok = True
            else:
                result.reason = (
                    f"remote content hash mismatch after re-read "
                    f"(local {local_sha[:12]} != remote {remote_sha[:12]})"
                )
        else:
            result.reason = "remote unavailable: local-only recovery commit"
            _local_recovery_commit(transport, files)
    except Exception as exc:
        result.reason = f"remote publish failed ({exc}); local-only recovery commit"
        _local_recovery_commit(transport, files)

    st_fields = {"note": f"publish: {result.mode} ({result.reason})"}
    state.update_fields(run_paths, **st_fields)
    state.record_artifact(run_paths, "publish-mode", result.mode)
    state.record_artifact(run_paths, "publish-sha256", result.remote_sha256 or local_sha)
    state.record_artifact(run_paths, "published-article", article_rel)
    if remote_ok:
        state.record_artifact(run_paths, "publish-verified", "remote-reread")
    return result


def _local_recovery_commit(transport, files: dict) -> None:
    """Best-effort local commit so the article is recoverable offline."""
    try:
        if isinstance(transport, GitTransport):
            transport.push(files)  # push() commits locally first; may raise on push
    except Exception:
        try:  # commit-only fallback when the push itself failed
            transport.ensure_repo()
            transport._git("add", "-A")
            transport._git(
                "-c", "user.name=AI Daily",
                "-c", "user.email=ai-daily@localhost",
                "commit", "-m", f"{PUBLISH_MESSAGE_PREFIX}: local-only recovery",
                check=False,
            )
        except Exception:
            pass
