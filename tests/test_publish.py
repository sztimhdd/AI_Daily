"""Tests for the GitHub publisher.

The publisher writes the article + recovery files into a publish repo,
pushes to a remote when one is reachable, then RE-READS the remote
content and hashes it to prove the publish.  When the remote is
unavailable it falls back to an explicit local-only mode — never a fake
remote success.  Tests never touch the real repository or network.
"""

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ai_daily import assemble, assemble_en, linkedin, paths, publish, state, topics, visuals

FIXTURES = pathlib.Path(__file__).resolve().parents[0] / "fixtures"

ARTICLE = """# AI 搜索预算与个人创作者的研究成本

独立创作者正在为搜索预算付出可计量的成本，见 [来源](https://source-a.example.com/posts/agent-search-cost)。
"""


class FakeTransport:
    """Injectable transport: records pushes, serves remote reads."""

    def __init__(self, available=True, push_raises=False, corrupt=False):
        self._available = available
        self._push_raises = push_raises
        self._corrupt = corrupt
        self.pushed = None

    def available(self):
        return self._available

    def push(self, files):
        if self._push_raises:
            raise RuntimeError("remote rejected the push")
        self.pushed = dict(files)

    def read_remote(self, relpath):
        data = self.pushed[relpath]
        return data + b"CORRUPTED" if self._corrupt else data


class PublishBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.rp = paths.RunPaths.for_date(self.root, "2026-08-12")
        self.rp.ensure_work_dir()
        state.init_state(self.rp)
        self.topic = topics.choose_fixture(self.rp, FIXTURES / "topic_fixture.json")
        self.repo_dir = self.root / "publish-repo"
        self.repo_dir.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def assemble_first(self):
        (self.rp.work_dir / "article.md").write_text(ARTICLE, encoding="utf-8")
        (self.rp.work_dir / "research.json").write_text(
            json.dumps({"questions": [], "evidence_urls": []}), encoding="utf-8"
        )
        assemble.run(self.rp)
        return self.rp.final_article_path(self.topic["slug"])

    def assemble_en_first(self):
        slug = "the-english-delivery-is-ready"
        (self.rp.work_dir / "article-en.md").write_text(
            "# The English delivery is ready\n\nA sourced point ([source](https://example.com/1)).\n",
            encoding="utf-8",
        )
        (self.rp.work_dir / "evidence-package.json").write_text(
            json.dumps({"sources": [{"url": "https://example.com/1", "title": "source"}]}),
            encoding="utf-8",
        )
        (self.rp.work_dir / linkedin.LINKEDIN_KIT_JSON).write_text(
            json.dumps({"seo_title": "English delivery", "seo_description": "A delivery test.", "post": "Post"}),
            encoding="utf-8",
        )
        (self.rp.work_dir / linkedin.LINKEDIN_KIT_MD).write_text("# Kit\n", encoding="utf-8")
        images = self.rp.work_dir / visuals.IMAGES_DIR
        images.mkdir()
        (images / "01.webp").write_bytes(b"RIFF....WEBP")
        (self.rp.work_dir / visuals.IMAGES_MANIFEST_JSON).write_text(
            json.dumps({"images": [{"id": "01", "status": "generated", "format": "webp", "width": 1, "height": 1}]}),
            encoding="utf-8",
        )
        state.update_fields(self.rp, en_title="The English delivery is ready", en_slug=slug)
        assemble_en.run(self.rp)
        return slug


class FakeTransportTests(PublishBase):
    def test_publish_en_uses_english_paths_and_full_package(self):
        slug = self.assemble_en_first()
        result = publish.publish_en(self.rp, repo_dir=self.repo_dir, transport=FakeTransport())
        self.assertEqual(result.mode, "remote")
        self.assertTrue(result.published_relpath.endswith("-en.md"))
        package = self.repo_dir / "outputs" / "2026" / "08" / "12" / slug
        self.assertTrue((package / "linkedin-kit.md").is_file())
        self.assertTrue((package / "images" / "01.webp").is_file())
    def test_remote_publish_rereads_and_hashes_content(self):
        final = self.assemble_first()
        result = publish.publish(
            self.rp, repo_dir=self.repo_dir, transport=FakeTransport()
        )
        self.assertTrue(result.ok, result.reason)
        self.assertEqual(result.mode, "remote")
        expected = hashlib.sha256(final.read_bytes()).hexdigest()
        self.assertEqual(result.remote_sha256, expected)
        st = state.read_state(self.rp)
        self.assertEqual(st["artifacts"]["publish-mode"], "remote")
        self.assertEqual(st["artifacts"]["publish-sha256"], expected)

    def test_recovery_files_written_to_repo_dir(self):
        self.assemble_first()
        publish.publish(self.rp, repo_dir=self.repo_dir, transport=FakeTransport())
        slug = self.topic["slug"]
        self.assertTrue((self.repo_dir / "articles" / f"2026-08-12-{slug}-zh.md").is_file())
        self.assertTrue(
            (self.repo_dir / "outputs" / "2026" / "08" / "12" / slug / "metadata.json").is_file()
        )
        self.assertTrue(
            (self.repo_dir / "outputs" / "2026" / "08" / "12" / slug / "sources.md").is_file()
        )

    def test_remote_unavailable_marks_local_only(self):
        self.assemble_first()
        result = publish.publish(
            self.rp, repo_dir=self.repo_dir, transport=FakeTransport(available=False)
        )
        self.assertTrue(result.ok, result.reason)
        self.assertEqual(result.mode, "local-only")
        self.assertEqual(result.remote_sha256, "")
        self.assertIn("unavailable", result.reason)
        st = state.read_state(self.rp)
        self.assertEqual(st["artifacts"]["publish-mode"], "local-only")
        self.assertNotIn("publish-sha256-remote", st["artifacts"])
        # local recovery commit content is still hashed for the record
        self.assertTrue(st["artifacts"]["publish-sha256"])

    def test_push_failure_falls_back_to_local_only(self):
        self.assemble_first()
        result = publish.publish(
            self.rp, repo_dir=self.repo_dir, transport=FakeTransport(push_raises=True)
        )
        self.assertEqual(result.mode, "local-only")
        self.assertIn("push", result.reason)

    def test_remote_hash_mismatch_is_not_fake_success(self):
        self.assemble_first()
        result = publish.publish(
            self.rp, repo_dir=self.repo_dir, transport=FakeTransport(corrupt=True)
        )
        self.assertEqual(result.mode, "local-only")
        self.assertEqual(result.remote_sha256, "")
        self.assertIn("mismatch", result.reason)

    def test_publish_requires_assembled_article(self):
        with self.assertRaises(publish.PublishError):
            publish.publish(self.rp, repo_dir=self.repo_dir, transport=FakeTransport())


def run_git(args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )


class GitTransportTests(PublishBase):
    """Real git against a temp bare remote — never the real repository."""

    def make_bare_remote(self):
        remote = self.root / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, check=True)
        return remote

    def test_git_push_then_reread_remote_hash(self):
        remote = self.make_bare_remote()
        final = self.assemble_first()
        transport = publish.GitTransport(
            self.repo_dir, remote_url=str(remote), branch="main"
        )
        result = publish.publish(self.rp, repo_dir=self.repo_dir, transport=transport)
        self.assertEqual(result.mode, "remote", result.reason)
        expected = hashlib.sha256(final.read_bytes()).hexdigest()
        self.assertEqual(result.remote_sha256, expected)
        # independent proof: read the article straight from the bare remote
        rel = f"articles/2026-08-12-{self.topic['slug']}-zh.md"
        shown = subprocess.run(
            ["git", "--git-dir", str(remote), "show", f"main:{rel}"],
            capture_output=True,
        )
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(hashlib.sha256(shown.stdout).hexdigest(), expected)

    def test_git_push_rebases_when_remote_moved_ahead(self):
        remote = self.make_bare_remote()
        self.assemble_first()
        transport = publish.GitTransport(
            self.repo_dir, remote_url=str(remote), branch="main"
        )
        publish.publish(self.rp, repo_dir=self.repo_dir, transport=transport)
        # Someone else commits to the remote after our first publish.
        other = self.root / "other"
        subprocess.run(
            ["git", "clone", str(remote), str(other)],
            capture_output=True, check=True,
        )
        (other / "unrelated.txt").write_text("moved ahead\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(other), "add", "-A"],
                       capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(other), "-c", "user.name=t",
             "-c", "user.email=t@t", "commit", "-m", "remote moved"],
            capture_output=True, check=True,
        )
        subprocess.run(["git", "-C", str(other), "push", "origin", "main"],
                       capture_output=True, check=True)
        # Local payload changes; a second publish must still reach the remote.
        (self.rp.work_dir / "article.md").write_text(
            ARTICLE + "\nUpdated paragraph.\n", encoding="utf-8"
        )
        assemble.run(self.rp)
        result = publish.publish(
            self.rp, repo_dir=self.repo_dir, transport=transport
        )
        self.assertEqual(result.mode, "remote", result.reason)

    def test_git_unreachable_remote_is_local_only(self):
        self.assemble_first()
        transport = publish.GitTransport(
            self.repo_dir, remote_url=str(self.root / "no-such-remote.git"), branch="main"
        )
        result = publish.publish(self.rp, repo_dir=self.repo_dir, transport=transport)
        self.assertEqual(result.mode, "local-only")
        self.assertEqual(result.remote_sha256, "")
        # local recovery commit exists
        log = run_git(["log", "--oneline"], self.repo_dir)
        self.assertIn("publish", log.stdout)


if __name__ == "__main__":
    unittest.main()
