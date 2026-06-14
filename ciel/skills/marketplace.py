"""
CIEL Skill Marketplace — catalogue, search, install, publish.

Deux sources :
  1. Catalogue distant (URL HTTP, fichier JSON)
  2. Catalogue embarqué (curated starter skills)

Intégré avec SkillManager pour l'installation locale.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ciel.skills.models import SkillManager

log = logging.getLogger("ciel.skills.marketplace")


@dataclass(slots=True)
class CatalogueEntry:
    id: str
    name: str
    description: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    body: str = ""
    author: str = "CIEL"
    url: str = ""
    stars: int = 0
    installs: int = 0
    source: str = "embedded"  # embedded | remote

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name,
            "description": self.description, "category": self.category,
            "tags": self.tags, "version": self.version,
            "author": self.author, "stars": self.stars,
            "installs": self.installs, "source": self.source,
        }


_BUILTIN_CATALOGUE: list[CatalogueEntry] = [
    CatalogueEntry(
        id="sk-builtin-web-scraper",
        name="web-scraper",
        description="Extract and structure data from web pages",
        category="data",
        tags=["web", "scraping", "html", "extract"],
        body=(
            "def web_scrape(url, selector=None):\n"
            '    """Fetch a URL and extract content.\n'
            "    Args:\n"
            "        url: The target URL\n"
            "        selector: Optional CSS selector\n"
            "    Returns:\n"
            "        dict with status, content, and metadata\n"
            '    """\n'
            "    import httpx\n"
            "    from bs4 import BeautifulSoup\n"
            "    r = httpx.get(url, timeout=30)\n"
            "    r.raise_for_status()\n"
            "    soup = BeautifulSoup(r.text, 'html.parser')\n"
            "    if selector:\n"
            "        elements = soup.select(selector)\n"
            "        return {'status': r.status_code, 'results': [e.get_text(strip=True) for e in elements]}\n"
            "    return {'status': r.status_code, 'title': soup.title.string if soup.title else ''}"
        ),
        author="CIEL",
        stars=42,
        installs=1280,
    ),
    CatalogueEntry(
        id="sk-builtin-code-reviewer",
        name="code-reviewer",
        description="Analyze source code for bugs, style issues, and improvements",
        category="dev",
        tags=["code", "review", "lint", "quality"],
        body=(
            "def code_review(file_path, language=None):\n"
            '    """Review a source file for common issues.\n'
            "    Returns list of findings with severity and line numbers.\n"
            '    """\n'
            "    import ast\n"
            "    findings = []\n"
            "    with open(file_path) as f:\n"
            "        source = f.read()\n"
            "    try:\n"
            "        tree = ast.parse(source)\n"
            "    except SyntaxError as e:\n"
            "        findings.append({'severity': 'error', 'msg': str(e)})\n"
            "        return findings\n"
            "    for node in ast.walk(tree):\n"
            "        if isinstance(node, ast.FunctionDef):\n"
            "            if not ast.get_docstring(node):\n"
            "                findings.append({'severity': 'warn', 'line': node.lineno, 'msg': 'Missing docstring'})\n"
            "    return findings"
        ),
        author="CIEL",
        stars=156,
        installs=3400,
    ),
    CatalogueEntry(
        id="sk-builtin-summarizer",
        name="text-summarizer",
        description="Summarize long texts using extractive techniques",
        category="nlp",
        tags=["text", "summarization", "nlp", "extractive"],
        body=(
            "def summarize(text, max_sentences=5):\n"
            '    """Extractive text summarization using sentence scoring.\n'
            "    Args:\n"
            "        text: Input text to summarize\n"
            "        max_sentences: Number of sentences in summary\n"
            "    Returns:\n"
            "        Summarized text\n"
            '    """\n'
            "    import re\n"
            "    from collections import Counter\n"
            "    sentences = re.split(r'(?<=[.!?])\\s+', text)\n"
            "    if len(sentences) <= max_sentences:\n"
            "        return text\n"
            "    words = re.findall(r'\\w+', text.lower())\n"
            "    freq = Counter(words)\n"
            "    scored = [(sum(freq[w] for w in re.findall(r'\\w+', s.lower()) if w in freq) / max(len(re.findall(r'\\w+', s)), 1), s) for s in sentences]\n"
            "    top = sorted(scored, key=lambda x: -x[0])[:max_sentences]\n"
            "    return ' '.join(s for _, s in sorted(top, key=lambda x: sentences.index(x[1])))"
        ),
        author="CIEL",
        stars=89,
        installs=2100,
    ),
    CatalogueEntry(
        id="sk-builtin-data-validator",
        name="data-validator",
        description="Validate data structures against schemas",
        category="data",
        tags=["data", "validation", "schema", "quality"],
        body=(
            "def validate(data, schema):\n"
            '    """Validate data against a JSON-like schema.\n'
            "    Schema format: {'field': {'type': 'str|int|float|list|dict', 'required': bool, 'min': num, 'max': num}}\n"
            '    Returns dict with valid bool and errors list.\n'
            '    """\n'
            "    errors = []\n"
            "    for field, rules in schema.items():\n"
            "        value = data.get(field)\n"
            "        if rules.get('required') and value is None:\n"
            "            errors.append(f'{field}: required')\n"
            "            continue\n"
            "        if value is None:\n"
            "            continue\n"
            "        expected = rules.get('type')\n"
            "        if expected and type(value).__name__ != expected:\n"
            "            errors.append(f'{field}: expected {expected}, got {type(value).__name__}')\n"
            "        if isinstance(value, (int, float)):\n"
            "            if 'min' in rules and value < rules['min']:\n"
            "                errors.append(f'{field}: below minimum {rules[\"min\"]}')\n"
            "            if 'max' in rules and value > rules['max']:\n"
            "                errors.append(f'{field}: above maximum {rules[\"max\"]}')\n"
            "    return {'valid': len(errors) == 0, 'errors': errors}"
        ),
        author="CIEL",
        stars=34,
        installs=890,
    ),
    CatalogueEntry(
        id="sk-builtin-file-organizer",
        name="file-organizer",
        description="Organize files by type, date, or custom rules",
        category="system",
        tags=["files", "organize", "cleanup", "system"],
        body=(
            "def organize(directory, by='type', dry_run=True):\n"
            '    """Organize files in a directory.\n'
            "    Args:\n"
            "        directory: Path to organize\n"
            "        by: 'type' | 'date' | 'size'\n"
            "        dry_run: If True, only print what would be done\n"
            "    Returns:\n"
            "        dict with moved count and summary\n"
            '    """\n'
            "    from pathlib import Path\n"
            "    import shutil\n"
            "    import mimetypes\n"
            "    base = Path(directory)\n"
            "    if not base.exists():\n"
            "        return {'moved': 0, 'error': 'Directory not found'}\n"
            "    moved = 0\n"
            "    for f in base.iterdir():\n"
            "        if f.is_dir() or f.name.startswith('.'):\n"
            "            continue\n"
            "        if by == 'type':\n"
            "            mime, _ = mimetypes.guess_type(f.name)\n"
            "            folder = (mime or 'unknown').split('/')[0]\n"
            "        elif by == 'date':\n"
            "            import time\n"
            "            folder = time.strftime('%Y-%m', time.localtime(f.stat().st_mtime))\n"
            "        else:\n"
            "            sz = f.stat().st_size\n"
            "            folder = 'large' if sz > 10*1024*1024 else 'medium' if sz > 1024*1024 else 'small'\n"
            "        target = base / folder\n"
            "        if not dry_run:\n"
            "            target.mkdir(exist_ok=True)\n"
            "            shutil.move(str(f), str(target / f.name))\n"
            "        moved += 1\n"
            "    return {'moved': moved, 'by': by, 'dry_run': dry_run}"
        ),
        author="CIEL",
        stars=67,
        installs=1750,
    ),
    CatalogueEntry(
        id="sk-builtin-api-tester",
        name="api-tester",
        description="Test HTTP APIs with assertions on status, headers, and body",
        category="dev",
        tags=["api", "testing", "http", "rest"],
        body=(
            "def test_api(url, method='GET', headers=None, body=None, expected_status=200, expected_contains=None):\n"
            '    """Test an HTTP API endpoint.\n'
            "    Returns dict with pass/fail, response details, and assertions.\n"
            '    """\n'
            "    import httpx\n"
            "    try:\n"
            "        r = httpx.request(method, url, headers=headers, json=body, timeout=30)\n"
            "        result = {'url': url, 'status': r.status_code, 'passed': True, 'assertions': []}\n"
            "        if r.status_code != expected_status:\n"
            "            result['passed'] = False\n"
            "            result['assertions'].append(f'Status: expected {expected_status}, got {r.status_code}')\n"
            "        if expected_contains:\n"
            "            text = r.text.lower()\n"
            "            for s in expected_contains if isinstance(expected_contains, list) else [expected_contains]:\n"
            "                if s.lower() not in text:\n"
            "                    result['passed'] = False\n"
            "                    result['assertions'].append(f'Body missing: {s}')\n"
            "        return result\n"
            "    except Exception as e:\n"
            "        return {'url': url, 'passed': False, 'error': str(e)}"
        ),
        author="CIEL",
        stars=53,
        installs=1400,
    ),
    CatalogueEntry(
        id="sk-builtin-json-transform",
        name="json-transform",
        description="Transform JSON data with JMESPath expressions",
        category="data",
        tags=["json", "transform", "jmespath", "data"],
        body=(
            "def json_transform(data, expression):\n"
            '    """Transform JSON/dict data using JMESPath.\n'
            "    Args:\n"
            "        data: Input dict or list\n"
            "        expression: JMESPath expression string\n"
            "    Returns:\n"
            "        Transformed result\n"
            '    """\n'
            "    try:\n"
            "        import jmespath\n"
            "        return jmespath.search(expression, data)\n"
            "    except ImportError:\nn"
            "        return _simple_transform(data, expression)\n"
            "def _simple_transform(data, expr):\n"
            '    """Fallback JMESPath-like transformer."""\n'
            "    parts = expr.split('.')\n"
            "    current = data\n"
            "    for p in parts:\n"
            "        if '[' in p and ']' in p:\n"
            "            name, idx = p.split('[')\n"
            "            idx = int(idx.rstrip(']'))\n"
            "            current = current.get(name, [])[idx] if isinstance(current, dict) else current[idx]\n"
            "        elif isinstance(current, dict):\n"
            "            current = current.get(p)\n"
            "        else:\n"
            "            return None\n"
            "    return current"
        ),
        author="CIEL",
        stars=28,
        installs=760,
    ),
    CatalogueEntry(
        id="sk-builtin-scheduler",
        name="task-scheduler",
        description="Simple in-process task scheduler with cron-like expressions",
        category="system",
        tags=["scheduler", "cron", "tasks", "automation"],
        body=(
            "import time\nimport threading\nfrom dataclasses import dataclass\n\n"
            "@dataclass\nclass ScheduledTask:\n"
            "    name: str\n    interval: int\n    func: callable\n    last_run: float = 0\n\n"
            "class TaskScheduler:\n"
            "    def __init__(self):\n"
            "        self._tasks = []\n"
            "        self._running = False\n"
            "        self._thread = None\n"
            "    def add(self, name, interval, func):\n"
            "        self._tasks.append(ScheduledTask(name, interval, func))\n"
            "    def start(self):\n"
            "        self._running = True\n"
            "        self._thread = threading.Thread(target=self._loop, daemon=True)\n"
            "        self._thread.start()\n"
            "    def stop(self):\n"
            "        self._running = False\n"
            "    def _loop(self):\n"
            "        while self._running:\n"
            "            now = time.time()\n"
            "            for t in self._tasks:\n"
            "                if now - t.last_run >= t.interval:\n"
            "                    try:\n"
            "                        t.func()\n"
            "                    except Exception as e:\n"
            "                        print(f'[Scheduler] {t.name} error: {e}')\n"
            "                    t.last_run = now\n"
            "            time.sleep(1)"
        ),
        author="CIEL",
        stars=45,
        installs=1100,
    ),
]


class SkillMarketplace:
    """Marketplace de compétences CIEL.

    Gère un catalogue (embarqué + distant), la recherche,
    l'installation, et la publication de skills.
    """

    def __init__(self, manager: SkillManager | None = None):
        self._manager = manager or SkillManager()
        self._catalogue: dict[str, CatalogueEntry] = {}
        self._remote_sources: list[str] = []
        self._on_install: Callable | None = None
        self._load_builtin()

    def _ensure_discovered(self) -> None:
        """Découvre les skills locaux si pas encore fait."""
        if not hasattr(self._manager, '_skills') or not self._manager._skills:
            self._manager.discover()

    def _load_builtin(self) -> None:
        for entry in _BUILTIN_CATALOGUE:
            self._catalogue[entry.id] = entry
        log.info("Loaded %d built-in catalogue entries", len(_BUILTIN_CATALOGUE))

    # ── Catalogue management ──

    def add_source(self, url: str) -> bool:
        """Ajoute une source distante au catalogue."""
        if url not in self._remote_sources:
            self._remote_sources.append(url)
            log.info("Added remote source: %s", url)
            return True
        return False

    def remove_source(self, url: str) -> bool:
        """Retire une source distante."""
        if url in self._remote_sources:
            self._remote_sources.remove(url)
            return True
        return False

    def list_sources(self) -> list[str]:
        return list(self._remote_sources)

    def refresh(self) -> int:
        """Recharge le catalogue depuis toutes les sources distantes."""
        import httpx
        count = 0
        for url in self._remote_sources:
            try:
                r = httpx.get(url, timeout=15)
                r.raise_for_status()
                entries = r.json()
                for e in entries:
                    entry = CatalogueEntry(
                        id=e.get("id", str(uuid.uuid4())),
                        name=e["name"],
                        description=e.get("description", ""),
                        category=e.get("category", "general"),
                        tags=e.get("tags", []),
                        version=e.get("version", "1.0.0"),
                        body=e.get("body", ""),
                        author=e.get("author", "unknown"),
                        url=url,
                        stars=e.get("stars", 0),
                        installs=e.get("installs", 0),
                        source="remote",
                    )
                    self._catalogue[entry.id] = entry
                    count += 1
                log.info("Fetched %d entries from %s", len(entries), url)
            except Exception as e:
                log.warning("Failed to fetch %s: %s", url, e)
        return count

    # ── Search ──

    def search(self, query: str = "", category: str = "",
               tag: str = "", min_stars: int = 0) -> list[CatalogueEntry]:
        """Cherche dans le catalogue."""
        results: list[CatalogueEntry] = []
        q = query.lower().strip()
        for entry in self._catalogue.values():
            if category and entry.category != category:
                continue
            if tag and tag not in entry.tags:
                continue
            if entry.stars < min_stars:
                continue
            if q:
                if (q in entry.name.lower()
                        or q in entry.description.lower()
                        or q in entry.id.lower()
                        or any(q in t.lower() for t in entry.tags)):
                    results.append(entry)
            else:
                results.append(entry)
        results.sort(key=lambda e: (-e.stars, -e.installs, e.name))
        return results

    def get(self, skill_id: str) -> CatalogueEntry | None:
        return self._catalogue.get(skill_id)

    def list_by_category(self, category: str) -> list[CatalogueEntry]:
        return self.search(category=category)

    def categories(self) -> list[dict[str, Any]]:
        cats: dict[str, dict[str, Any]] = {}
        for entry in self._catalogue.values():
            if entry.category not in cats:
                cats[entry.category] = {"name": entry.category, "count": 0}
            cats[entry.category]["count"] += 1
        return sorted(cats.values(), key=lambda c: -c["count"])

    def stats(self) -> dict[str, Any]:
        return {
            "total": len(self._catalogue),
            "categories": len(self.categories()),
            "sources": len(self._remote_sources),
            "builtin": len(_BUILTIN_CATALOGUE),
        }

    # ── Install ──

    def install(self, skill_id: str, category: str | None = None) -> str | None:
        """Installe un skill du catalogue dans le gestionnaire local.

        Returns:
            L'ID local du skill installé, ou None si échec.
        """
        entry = self._catalogue.get(skill_id)
        if not entry:
            log.warning("Skill %s not found in catalogue", skill_id)
            return None

        local = self._manager.create(
            name=entry.name,
            description=entry.description,
            body=entry.body,
            category=category or entry.category,
            tags=list(entry.tags),
        )
        log.info("Installed skill %s -> local %s", skill_id, local.id)

        if self._on_install:
            self._on_install(entry, local)

        return local.id

    def on_install(self, cb: Callable) -> None:
        self._on_install = cb

    def install_many(self, skill_ids: list[str]) -> dict[str, str | None]:
        return {sid: self.install(sid) for sid in skill_ids}

    # ── Publish ──

    def publish(self, skill_id: str, author: str = "CIEL",
                export_path: str | None = None) -> dict[str, Any] | None:
        """Exporte un skill local vers le format catalogue (pour publication)."""
        self._ensure_discovered()
        skill = self._manager.get(skill_id)
        if not skill:
            # chercher par nom
            skills = self._manager.list()
            skill = next((s for s in skills if s.name == skill_id), None)
        if not skill:
            log.warning("Skill %s not found locally", skill_id)
            return None

        export = {
            "id": f"sk-{skill.name.lower().replace(' ', '-')}",
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "tags": skill.tags,
            "version": skill.version,
            "body": skill.body,
            "author": author,
            "stars": 0,
            "installs": 0,
        }

        if export_path:
            path = Path(export_path)
            path.write_text(json.dumps(export, indent=2), encoding="utf-8")
            log.info("Exported skill %s to %s", skill.name, export_path)

        return export

    # ── Popularity / tracking ──

    def record_install(self, catalogue_id: str) -> None:
        entry = self._catalogue.get(catalogue_id)
        if entry:
            entry.installs += 1

    def record_star(self, catalogue_id: str) -> None:
        entry = self._catalogue.get(catalogue_id)
        if entry:
            entry.stars += 1
