"""Debug skills framework — reusable debugging knowledge base."""

from __future__ import annotations

import re
from pathlib import Path

from debugforge.server import mcp
from debugforge.state import config


def _get_skills_dir() -> Path | None:
    """Get the skills directory path, or None if not configured/found."""
    if config.skills_dir:
        p = Path(config.skills_dir)
        if p.is_dir():
            return p
    # Fallback: look for .debugforge/skills relative to config dir
    if config.config_dir:
        p = Path(config.config_dir) / ".debugforge" / "skills"
        if p.is_dir():
            return p
    return None


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    # Simple YAML parsing (key: value and key: [list])
    meta = {}
    current_key = None
    current_list = None

    for line in frontmatter_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item
        if stripped.startswith("- ") and current_key:
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip())
            meta[current_key] = current_list
            continue

        # Key-value pair
        if ":" in stripped:
            if current_list is not None:
                current_list = None
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            current_key = key
            if val:
                meta[key] = val
            else:
                current_list = []
                meta[key] = current_list

    return meta, body


def _load_skill(path: Path) -> dict | None:
    """Load a single skill file and return its metadata + content."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return None

    meta, body = _parse_frontmatter(content)
    name = meta.get("name", path.stem)
    return {
        "name": name,
        "file": path.name,
        "category": meta.get("category", "general"),
        "severity": meta.get("severity", ""),
        "target": meta.get("target", ""),
        "keywords": meta.get("keywords", []),
        "body": body,
        "raw": content,
    }


@mcp.tool()
async def list_debug_skills() -> str:
    """List all available debug skills in the project knowledge base.

    Returns skill names, categories, and brief descriptions from
    the configured skills directory.

    Returns:
        Formatted list of available debug skills
    """
    skills_dir = _get_skills_dir()
    if skills_dir is None:
        return (
            "No debug skills found. Create a skills directory:\n"
            "  1. Set [debug] skills_dir in debugforge.toml\n"
            "  2. Or create .debugforge/skills/ in your project root\n"
            "  3. Add .md skill files (see debugforge-workflow.md for format)"
        )

    skills = []
    for path in sorted(skills_dir.glob("*.md")):
        skill = _load_skill(path)
        if skill:
            skills.append(skill)

    if not skills:
        return f"Skills directory exists ({skills_dir}) but contains no .md files."

    lines = [f"# Debug Skills ({len(skills)} available)", ""]
    for s in skills:
        category = f"[{s['category']}]" if s['category'] else ""
        severity = f" ({s['severity']})" if s['severity'] else ""
        keywords = ", ".join(s["keywords"][:4]) if s["keywords"] else ""
        lines.append(f"- **{s['name']}** {category}{severity}")
        if keywords:
            lines.append(f"  Keywords: {keywords}")

    return "\n".join(lines)


@mcp.tool()
async def get_debug_skill(name: str) -> str:
    """Get the full content of a specific debug skill.

    Args:
        name: Skill name or filename (e.g., "stack-overflow" or "stack-overflow.md")

    Returns:
        Full skill content including symptoms, debug strategy, root causes, and fix patterns
    """
    skills_dir = _get_skills_dir()
    if skills_dir is None:
        return "Error: No skills directory configured."

    # Try exact filename match
    target = name if name.endswith(".md") else f"{name}.md"
    path = skills_dir / target
    if path.exists():
        skill = _load_skill(path)
        if skill:
            return skill["raw"]

    # Try matching by name in frontmatter
    for p in skills_dir.glob("*.md"):
        skill = _load_skill(p)
        if skill and skill["name"] == name:
            return skill["raw"]

    available = [p.stem for p in skills_dir.glob("*.md")]
    return f"Skill '{name}' not found. Available: {', '.join(available)}"


@mcp.tool()
async def search_debug_skills(keywords: str) -> str:
    """Search debug skills by keywords matching symptoms or categories.

    Searches through skill names, keywords, categories, and content body.

    Args:
        keywords: Space-separated search terms (e.g., "HardFault stack crash")

    Returns:
        Matching skills with relevance ranking
    """
    skills_dir = _get_skills_dir()
    if skills_dir is None:
        return "No skills directory configured."

    search_terms = [t.lower() for t in keywords.split() if t]
    if not search_terms:
        return "Error: Provide at least one search keyword."

    results = []
    for path in skills_dir.glob("*.md"):
        skill = _load_skill(path)
        if not skill:
            continue

        # Score: count how many search terms match
        searchable = " ".join([
            skill["name"],
            skill["category"],
            " ".join(skill["keywords"]),
            skill["body"][:500],
        ]).lower()

        score = sum(1 for term in search_terms if term in searchable)
        if score > 0:
            results.append((score, skill))

    if not results:
        return f"No skills match keywords: {keywords}"

    results.sort(key=lambda x: x[0], reverse=True)

    lines = [f"# Search Results for: {keywords}", ""]
    for score, s in results[:5]:
        lines.append(f"- **{s['name']}** [{s['category']}] (relevance: {score}/{len(search_terms)})")
        if s["keywords"]:
            lines.append(f"  Keywords: {', '.join(s['keywords'][:5])}")
    lines.append("")
    lines.append("Use get_debug_skill(name) to read the full skill content.")

    return "\n".join(lines)


@mcp.tool()
async def save_debug_skill(
    name: str,
    category: str,
    keywords: str,
    symptoms: str,
    strategy: str,
    root_causes: str,
    fix_patterns: str,
) -> str:
    """Save a new debug skill to the knowledge base.

    Call this after successfully debugging a new type of issue to capture
    the experience for future reuse.

    Args:
        name: Short kebab-case name (e.g., "dma-transfer-timeout")
        category: Category — memory, fault, peripheral, timing, rtos, general
        keywords: Comma-separated keywords for search matching
        symptoms: Description of observable symptoms (what the user sees)
        strategy: Step-by-step debug strategy that worked
        root_causes: Common root causes for this type of issue
        fix_patterns: Patterns for fixing this type of issue

    Returns:
        Confirmation with the saved file path
    """
    skills_dir = _get_skills_dir()
    if skills_dir is None:
        # Create default location
        if config.config_dir:
            skills_dir = Path(config.config_dir) / ".debugforge" / "skills"
        else:
            skills_dir = Path.cwd() / ".debugforge" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize name
    safe_name = re.sub(r"[^a-z0-9-]", "-", name.lower().strip())
    filepath = skills_dir / f"{safe_name}.md"

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    keywords_yaml = "\n".join(f"  - {k}" for k in keyword_list)

    content = f"""---
name: {safe_name}
category: {category}
keywords:
{keywords_yaml}
---

# {name.replace('-', ' ').title()}

## Symptoms
{symptoms}

## Debug Strategy
{strategy}

## Common Root Causes
{root_causes}

## Fix Patterns
{fix_patterns}
"""

    try:
        filepath.write_text(content, encoding="utf-8")
        return f"Debug skill saved: {filepath}"
    except Exception as e:
        return f"Error saving skill: {e}"
