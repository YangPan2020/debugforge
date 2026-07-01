"""Tests for debug skills framework."""

from __future__ import annotations

import pytest

from debugforge.tools.skills import (
    _get_skills_dir,
    _load_skill,
    _parse_frontmatter,
)


class TestParseFrontmatter:
    def test_parses_basic_frontmatter(self):
        content = "---\nname: test-skill\ncategory: memory\n---\n# Body"
        meta, body = _parse_frontmatter(content)
        assert meta["name"] == "test-skill"
        assert meta["category"] == "memory"
        assert body == "# Body"

    def test_parses_list_keywords(self):
        content = "---\nname: x\nkeywords:\n  - foo\n  - bar\n---\nBody text"
        meta, body = _parse_frontmatter(content)
        assert meta["keywords"] == ["foo", "bar"]
        assert body == "Body text"

    def test_no_frontmatter(self):
        content = "Just regular markdown content"
        meta, body = _parse_frontmatter(content)
        assert meta == {}
        assert body == content

    def test_empty_content(self):
        meta, body = _parse_frontmatter("")
        assert meta == {}
        assert body == ""


class TestLoadSkill:
    def test_loads_skill_file(self, tmp_path):
        skill_file = tmp_path / "test-skill.md"
        skill_file.write_text(
            "---\nname: test-skill\ncategory: memory\n"
            "severity: high\nkeywords:\n  - crash\n  - stack\n---\n"
            "# Test Skill\n\n## Symptoms\nCrash on boot"
        )
        skill = _load_skill(skill_file)
        assert skill is not None
        assert skill["name"] == "test-skill"
        assert skill["category"] == "memory"
        assert skill["severity"] == "high"
        assert skill["keywords"] == ["crash", "stack"]
        assert "Crash on boot" in skill["body"]

    def test_loads_skill_without_frontmatter(self, tmp_path):
        skill_file = tmp_path / "plain.md"
        skill_file.write_text("# Plain skill\n\nNo frontmatter here")
        skill = _load_skill(skill_file)
        assert skill is not None
        assert skill["name"] == "plain"
        assert skill["category"] == "general"

    def test_nonexistent_file(self, tmp_path):
        skill = _load_skill(tmp_path / "missing.md")
        assert skill is None


class TestGetSkillsDir:
    def test_returns_none_when_not_configured(self, monkeypatch):
        from debugforge.state import config as real_config
        monkeypatch.setattr(real_config, "skills_dir", "")
        monkeypatch.setattr(real_config, "_base_dir", "")
        result = _get_skills_dir()
        assert result is None

    def test_returns_configured_dir(self, tmp_path, monkeypatch):
        from debugforge.state import config as real_config
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        monkeypatch.setattr(real_config, "skills_dir", str(skills_dir))
        result = _get_skills_dir()
        assert result == skills_dir

    def test_falls_back_to_debugforge_skills(self, tmp_path, monkeypatch):
        from debugforge.state import config as real_config
        skills_dir = tmp_path / ".debugforge" / "skills"
        skills_dir.mkdir(parents=True)
        monkeypatch.setattr(real_config, "skills_dir", "")
        monkeypatch.setattr(real_config, "_base_dir", str(tmp_path))
        result = _get_skills_dir()
        assert result == skills_dir
